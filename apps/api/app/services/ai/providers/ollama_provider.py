"""Ollama (local LLM) provider.

Ollama runs a local OpenAI-compatible chat endpoint at ``$OLLAMA_BASE_URL/v1``.
We hit the native /api/chat endpoint instead so we get reliable usage stats.
Treat the local fallback as "always available, free, slower". If Ollama isn't
running the connect will fail and the router will give up gracefully.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.services.ai.providers.base import (
    AIProvider,
    PermanentProviderError,
    TransientProviderError,
)
from app.services.ai.types import AIMessage, AIResponse


def _price_pence(input_tokens: int, output_tokens: int) -> int:
    gbp_input = (input_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_INPUT_PER_MTOKEN_OLLAMA
    gbp_output = (output_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_OUTPUT_PER_MTOKEN_OLLAMA
    return int(round((gbp_input + gbp_output) * 100))


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL

    def available(self) -> bool:
        # We can't cheaply check the daemon is running without a request, so we
        # report available iff the base URL is set. The actual call will raise
        # TransientProviderError if the daemon is down, letting the router
        # surface it cleanly.
        return bool(self.base_url)

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
        chosen_model = model or self.default_model

        payload: dict[str, Any] = {
            "model": chosen_model,
            "messages": [
                {"role": m.get("role", "user"), "content": m.get("content", "") or ""}
                for m in messages
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as exc:
            raise TransientProviderError(f"ollama transport: {exc!r}") from exc

        if resp.status_code >= 500:
            raise TransientProviderError(f"ollama 5xx: {resp.status_code} {resp.text[:200]}")
        if resp.status_code >= 400:
            raise PermanentProviderError(f"ollama 4xx: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)
        message = data.get("message", {}) or {}
        content = (message.get("content") or "").strip()
        input_tokens = int(data.get("prompt_eval_count", 0))
        output_tokens = int(data.get("eval_count", 0))

        return AIResponse(
            content=content,
            provider=self.name,
            model=chosen_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_pence=_price_pence(input_tokens, output_tokens),
            latency_ms=latency_ms,
            finish_reason=data.get("done_reason"),
            tool_calls=[],
            raw={"total_duration": data.get("total_duration")},
        )
