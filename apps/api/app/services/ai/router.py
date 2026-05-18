"""Hybrid AI router with multi-provider failover, retry, and cost tracking."""
from __future__ import annotations

import asyncio
import logging
import uuid
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.services.ai.providers.anthropic_provider import AnthropicProvider
from app.services.ai.providers.base import (
    AIProvider,
    PermanentProviderError,
    TransientProviderError,
)
from app.services.ai.providers.ollama_provider import OllamaProvider
from app.services.ai.providers.openai_provider import OpenAIProvider
from app.services.ai.types import AIMessage, AIResponse, AIRouterError

logger = logging.getLogger(__name__)


_PROVIDER_FACTORIES: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


class HybridAIRouter:
    """Try providers in configured order; persist a usage event on success.

    Persistence is best-effort: if the DB session can't be obtained (e.g. we're
    inside the very-early bootstrap before the DB is ready) the call still
    succeeds but we log a warning. Usage events are never on the critical path.
    """

    def __init__(self, providers: list[AIProvider]) -> None:
        self._providers = providers
        self._max_retries = max(0, int(settings.AI_MAX_RETRIES_PER_PROVIDER))
        self._timeout = float(settings.AI_REQUEST_TIMEOUT_SECONDS)

    @property
    def providers(self) -> list[AIProvider]:
        return list(self._providers)

    async def chat(
        self,
        messages: list[AIMessage],
        *,
        tenant_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        purpose: str = "general",
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
        record_usage: bool = True,
    ) -> AIResponse:
        attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None

        for fallback_depth, provider in enumerate(self._providers):
            if not provider.available():
                attempts.append({"provider": provider.name, "error": "unavailable"})
                continue

            for attempt in range(self._max_retries + 1):
                try:
                    response = await asyncio.wait_for(
                        provider.chat(
                            messages,
                            model=model,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            tools=tools,
                            timeout=self._timeout,
                        ),
                        timeout=self._timeout + 5,
                    )
                except asyncio.TimeoutError as exc:
                    last_error = exc
                    attempts.append({
                        "provider": provider.name,
                        "attempt": attempt,
                        "error": "timeout",
                    })
                    continue
                except TransientProviderError as exc:
                    last_error = exc
                    attempts.append({
                        "provider": provider.name,
                        "attempt": attempt,
                        "error": "transient",
                        "detail": str(exc)[:200],
                    })
                    continue
                except PermanentProviderError as exc:
                    last_error = exc
                    attempts.append({
                        "provider": provider.name,
                        "attempt": attempt,
                        "error": "permanent",
                        "detail": str(exc)[:200],
                    })
                    break  # No point retrying a 4xx; fall through to next provider
                except Exception as exc:  # pragma: no cover — defensive
                    last_error = exc
                    attempts.append({
                        "provider": provider.name,
                        "attempt": attempt,
                        "error": "unexpected",
                        "detail": str(exc)[:200],
                    })
                    break

                # Success
                logger.info(
                    "AI ok: purpose=%s provider=%s model=%s tokens=%s+%s cost=%spp lat=%sms fb=%s",
                    purpose, response.provider, response.model,
                    response.input_tokens, response.output_tokens,
                    response.cost_pence, response.latency_ms, fallback_depth,
                )
                if record_usage:
                    await self._record_usage(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        purpose=purpose,
                        response=response,
                        fallback_depth=fallback_depth,
                        status="success",
                        error=None,
                        attempts=attempts,
                    )
                return response

        # Everything failed
        logger.error("AI exhausted all providers: purpose=%s attempts=%s", purpose, attempts)
        if record_usage:
            await self._record_usage(
                tenant_id=tenant_id,
                user_id=user_id,
                purpose=purpose,
                response=None,
                fallback_depth=len(self._providers),
                status="failed",
                error=str(last_error) if last_error else "no providers available",
                attempts=attempts,
            )
        raise AIRouterError(
            f"All AI providers failed for purpose '{purpose}'", attempts=attempts,
        )

    # ── Persistence ──────────────────────────────────────────────────────

    async def _record_usage(
        self,
        *,
        tenant_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        purpose: str,
        response: AIResponse | None,
        fallback_depth: int,
        status: str,
        error: str | None,
        attempts: list[dict[str, Any]],
    ) -> None:
        try:
            from app.core.database import get_db_context
            from app.services.ai.models import AIUsageEvent

            async with get_db_context() as db:
                event = AIUsageEvent(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    purpose=purpose,
                    provider=response.provider if response else "n/a",
                    model=response.model if response else "n/a",
                    input_tokens=response.input_tokens if response else 0,
                    output_tokens=response.output_tokens if response else 0,
                    cost_pence=response.cost_pence if response else 0,
                    latency_ms=response.latency_ms if response else 0,
                    fallback_depth=fallback_depth,
                    status=status,
                    error_message=error,
                    extra={"attempts": attempts},
                )
                db.add(event)
                await db.commit()
        except Exception as exc:
            logger.warning("AI usage event persistence failed: %s", exc)


# ── Public factory ──────────────────────────────────────────────────────────

@lru_cache
def get_ai_router() -> HybridAIRouter:
    """Build a router from the configured provider order. Cached per process."""
    providers: list[AIProvider] = []
    seen: set[str] = set()
    for name in settings.ai_provider_order_list:
        if name in seen:
            continue
        seen.add(name)
        factory = _PROVIDER_FACTORIES.get(name)
        if factory is None:
            logger.warning("Unknown AI provider in AI_PROVIDER_ORDER: %s", name)
            continue
        providers.append(factory())

    # Always include Ollama as last-resort if nothing else is configured.
    if not providers:
        providers.append(OllamaProvider())

    return HybridAIRouter(providers)
