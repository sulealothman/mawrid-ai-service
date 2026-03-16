from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from app.prompts.base import PromptBuilder
from app.providers.ai_provider import AIProvider
from app.providers.schemas import Usage


async def generate_title(
    ai: AIProvider,
    history: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 20,
) -> Tuple[str, Optional[Usage]]:

    messages = PromptBuilder.build_title_from_history(
        history=[m for m in history if m.get("content" or "").strip()]
    )

    response = await ai.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    title = (response.text or "").strip().replace('"', '')
    return title, response.usage