"""Anthropic (Claude) provider."""
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
    gbp_input = (input_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_INPUT_PER_MTOKEN_ANTHROPIC
    gbp_output = (output_tokens / 1_000_000.0) * settings.AI_PRICE_GBP_OUTPUT_PER_MTOKEN_ANTHROPIC
    return int(round((gbp_input + gbp_output) * 100))


def _split_system(messages: list[AIMessage]) -> tuple[str | None, list[dict[str, Any]]]:
    """Anthropic takes `system` as a top-level field; flatten it out."""
    system_parts: list[str] = []
    remaining: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "system":
            system_parts.append(content or "")
        elif role in ("user", "assistant"):
            remaining.append({"role": role, "content": content})
        # tool messages: minimal support — render as user
        elif role == "tool":
            remaining.append({"role": "user", "content": f"[tool result]\n{content}"})
    system = "\n\n".join(p for p in system_parts if p).strip() or None
    return system, remaining


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self) -> None:
        self.default_model = settings.ANTHROPIC_MODEL

    def available(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

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
        system, msg_list = _split_system(messages)

        payload: dict[str, Any] = {
            "model": chosen_model,
            "messages": msg_list,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        if tools:
            # Anthropic tool schema is slightly different but a permissive
            # pass-through works for OpenAI-style function specs.
            payload["tools"] = tools

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            raise TransientProviderError(f"anthropic transport: {exc!r}") from exc

        if resp.status_code >= 500:
            raise TransientProviderError(f"anthropic 5xx: {resp.status_code} {resp.text[:200]}")
        if resp.status_code == 429:
            raise TransientProviderError(f"anthropic rate-limited: {resp.text[:200]}")
        if resp.status_code >= 400:
            raise PermanentProviderError(f"anthropic 4xx: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        # Concatenate text blocks; ignore non-text content (tool_use etc.) for now.
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for block in data.get("content", []):
            kind = block.get("type")
            if kind == "text":
                text_parts.append(block.get("text", ""))
            elif kind == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": __import__("json").dumps(block.get("input", {})),
                    },
                })
        content = "".join(text_parts).strip()

        usage = data.get("usage", {}) or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))

        return AIResponse(
            content=content,
            provider=self.name,
            model=chosen_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_pence=_price_pence(input_tokens, output_tokens),
            latency_ms=latency_ms,
            finish_reason=data.get("stop_reason"),
            tool_calls=tool_calls,
            raw={"id": data.get("id")},
        )
