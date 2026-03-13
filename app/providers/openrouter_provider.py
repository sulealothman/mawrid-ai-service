from __future__ import annotations

import json
from typing import AsyncIterator, Any, Optional

import httpx

from app.core.config import settings
from app.providers.ai_provider import AIProvider
from app.providers.schemas import EmbeddingResult, ChatResult, Usage


class OpenRouterProvider(AIProvider):
    """Provider for OpenRouter's OpenAI-compatible API.

    Expected base_url example: https://openrouter.ai/api/v1
    """

    def __init__(self) -> None:
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.api_key = settings.AI_API_KEY
        self.chat_model = settings.AI_CHAT_MODEL
        self.embed_model = settings.AI_EMBED_MODEL

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter asks for these (optional but recommended)
            "HTTP-Referer": getattr(settings, "APP_URL", ""),
            "X-Title": getattr(settings, "APP_TITLE", ""),
        }

        # Keep one client for connection pooling + performance
        self.client = httpx.AsyncClient(timeout=120)

    # ---------------- EMBEDDING ---------------- #

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        r = await self.client.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json={
                "model": self.embed_model,
                "input": texts,
            },
        )
        r.raise_for_status()
        j: dict[str, Any] = r.json()

        vectors = [item["embedding"] for item in (j.get("data") or [])]
        usage = self._parse_usage(j.get("usage"))
        return EmbeddingResult(vectors=vectors, usage=usage)

    # ---------------- CHAT (NON-STREAM) ---------------- #

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> ChatResult:

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        r = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        )
        r.raise_for_status()
        j: dict[str, Any] = r.json()

        text = (
            (j.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        return ChatResult(
            text=text or "",
            usage=self._parse_usage(j.get("usage")),
            model=(j.get("model") or self.chat_model),
        )

    # ---------------- STREAMING ---------------- #

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        ) as resp:
            resp.raise_for_status()

            async for line in resp.aiter_lines():
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue

                data = line.removeprefix("data:").strip()
                if data == "[DONE]":
                    break

                chunk = self._parse_stream_chunk(data)
                if chunk:
                    yield chunk

    # ---------------- LIFECYCLE ---------------- #

    async def close(self) -> None:
        await self.client.aclose()

    # ---------------- INTERNAL ---------------- #

    @staticmethod
    def _parse_stream_chunk(data: str) -> str | None:
        try:
            j = json.loads(data)
            delta = (j.get("choices") or [{}])[0].get("delta", {})
            return delta.get("content")
        except Exception:
            return None

    @staticmethod
    def _parse_usage(usage_obj: Any) -> Optional[Usage]:
        if not isinstance(usage_obj, dict):
            return None
        try:
            prompt = int(usage_obj.get("prompt_tokens") or 0)
            completion = int(usage_obj.get("completion_tokens") or 0)
            total = int(usage_obj.get("total_tokens") or (prompt + completion))
            return Usage(
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=total,
            )
        except Exception:
            return None
