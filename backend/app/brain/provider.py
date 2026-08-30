"""
Phase 1: the model provider abstraction.

Everything in app/agent/ talks to this interface only. Today the sole
implementation is OllamaProvider (local, no API keys). Phase 17's fine-tuned
JARVIS model becomes a new class implementing the same interface — nothing
above this layer changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> str:
        """Return the model's raw text completion for the given conversation.

        `messages` is a list of {"role": "user"|"assistant", "content": str}.
        If json_mode is True, the provider should instruct the model to
        return only valid JSON with no surrounding prose.
        """
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return a small dict describing whether the model backend is reachable."""
        raise NotImplementedError
