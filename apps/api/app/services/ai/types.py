"""Public types for the AI router."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict


# Mirrors the OpenAI / Anthropic chat message shape so providers can pass
# through without translation in the common case.
class AIMessage(TypedDict, total=False):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str
    tool_call_id: str
    tool_calls: list[dict[str, Any]]


@dataclass
class AIResponse:
    """Provider-agnostic chat completion result."""

    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_pence: int
    latency_ms: int
    finish_reason: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class AIRouterError(RuntimeError):
    """Raised when every provider in the router chain failed."""

    def __init__(self, message: str, *, attempts: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts or []
