"""OpenAI chat completion provider."""
from __future__ import annotations

import time
from typing import Any

from app.core.config import settings
from app.services.ai.providers.base import (
    AIProvider,
    PermanentProviderError,
    TransientProviderError,
)
from app.services.ai.types import AIMessage, AIResponse


def _price_pence(input_tokens: int, output_tokens: int) -> int:
    """Compute the cost in integer pence using settings' £/MTok prices."""
    gbp_input = (input_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_INPUT_PER_MTOKEN_OPENAI
    gbp_output = (output_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_OUTPUT_PER_MTOKEN_OPENAI
    return int(round((gbp_input + gbp_output) * 100))


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        self._client = None
        self.default_model = settings.OPENAI_MODEL

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def available(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    async def chat(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 30.0,
    ) -> AIResponse:
        from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, RateLimitError

        client = self._get_client()
        chosen_model = model or self.default_model

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": list(messages),
            "temperature": temperature,
            "timeout": timeout,
        }
        if max_tokens is not None:
            # gpt-4o / gpt-4o-mini reject legacy max_tokens on chat completions
            kwargs["max_completion_tokens"] = max_tokens
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        started = time.perf_counter()
        try:
            response = await client.chat.completions.create(**kwargs)
        except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
            raise TransientProviderError(f"openai transient: {exc!r}") from exc
        except APIStatusError as exc:
            # 5xx → transient; 4xx → permanent
            status = getattr(exc, "status_code", 0) or 0
            body = getattr(exc, "body", None)
            detail = f"openai HTTP {status}"
            if isinstance(body, dict) and body.get("error"):
                err = body["error"]
                if isinstance(err, dict):
                    detail = f"{detail}: {err.get('message', err)}"
                else:
                    detail = f"{detail}: {err}"
            elif exc.message:
                detail = f"{detail}: {exc.message}"
            if 500 <= status < 600:
                raise TransientProviderError(detail) from exc
            raise PermanentProviderError(detail) from exc
        except APIError as exc:
            raise TransientProviderError(f"openai api: {exc!r}") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        choice = response.choices[0]
        message = choice.message

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        tool_calls: list[dict[str, Any]] = []
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": getattr(tc, "type", "function"),
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return AIResponse(
            content=(message.content or "").strip(),
            provider=self.name,
            model=chosen_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_pence=_price_pence(input_tokens, output_tokens),
            latency_ms=latency_ms,
            finish_reason=choice.finish_reason,
            tool_calls=tool_calls,
            raw={"id": response.id},
        )
