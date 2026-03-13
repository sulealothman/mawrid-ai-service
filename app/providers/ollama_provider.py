from __future__ import annotations

import json
from typing import AsyncIterator, Any

import httpx

from app.core.config import settings
from app.providers.ai_provider import AIProvider
from app.providers.schemas import EmbeddingResult, ChatResult


class OllamaProvider(AIProvider):
    """Provider for Ollama API.

    Expected base_url example: http://localhost:11434
    """

    def __init__(self) -> None:
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.chat_model = settings.AI_CHAT_MODEL
        self.embed_model = settings.AI_EMBED_MODEL

        # Reusable client for performance
        self.client = httpx.AsyncClient(timeout=300)

    # ---------------- EMBEDDING ---------------- #

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        vectors: list[list[float]] = []

        # Ollama embeddings endpoint is per-text (prompt)
        for text in texts:
            r = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text,
                },
            )
            r.raise_for_status()
            j: dict[str, Any] = r.json()
            vectors.append(j.get("embedding") or [])

        # Ollama does not return token usage
        return EmbeddingResult(vectors=vectors, usage=None)

    # ---------------- CHAT (NON-STREAM) ---------------- #

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> ChatResult:

        options: dict[str, Any] = {"temperature": temperature}
        # In Ollama: num_predict is the max tokens to generate
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        r = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        r.raise_for_status()
        j: dict[str, Any] = r.json()

        text = (j.get("message") or {}).get("content", "")

        return ChatResult(
            text=text or "",
            usage=None,
            model=self.chat_model,
        )

    # ---------------- STREAMING ---------------- #

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": True,
            "options": options,
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
        ) as resp:
            resp.raise_for_status()

            async for line in resp.aiter_lines():
                if not line:
                    continue

                # Ollama streams JSON per line
                try:
                    j = json.loads(line)
                except Exception:
                    continue

                # Final message sometimes includes done=true
                msg = j.get("message") or {}
                token = msg.get("content")
                if token:
                    yield token

                if j.get("done") is True:
                    break

    # ---------------- LIFECYCLE ---------------- #

    async def close(self) -> None:
        await self.client.aclose()
