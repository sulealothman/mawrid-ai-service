from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.providers.schemas import EmbeddingResult, ChatResult


class AIProvider(ABC):

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResult:
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> ChatResult:
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        ...

    async def close(self) -> None:
        """Optional cleanup hook for providers that keep a long-lived client."""
        return None
