"""Provider abstraction.

Every concrete provider implements `available()` and `chat()`. The router
inspects `available()` (a cheap check — usually "is the API key set") before
trying a provider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.services.ai.types import AIMessage, AIResponse


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """Cheap check: is this provider configured/usable?"""

    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 30.0,
    ) -> AIResponse: ...


# Errors that should trigger fallback to the next provider rather than raising
# straight to the caller. Anything *not* in this list is treated as a bug and
# bubbles up.
class TransientProviderError(Exception):
    """The provider returned a 5xx / rate limit / timeout. Try the next one."""


class PermanentProviderError(Exception):
    """The provider returned a 4xx or invalid response. Fall back but don't retry."""
