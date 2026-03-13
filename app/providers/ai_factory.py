from __future__ import annotations

from app.core.config import settings
from app.providers.ai_provider import AIProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.ollama_provider import OllamaProvider


def get_ai_provider() -> AIProvider:
    provider = settings.AI_PROVIDER.lower()

    if provider == "openrouter":
        return OpenRouterProvider()

    if provider == "ollama":
        return OllamaProvider()

    raise ValueError(f"Unsupported AI provider: {provider}")
