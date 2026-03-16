from __future__ import annotations

from typing import AsyncIterator, Dict, List, Tuple

from app.providers.ai_provider import AIProvider
from app.providers.schemas import ChatResult
from app.domain.prompts.message_builder import build_rag_messages
from app.domain.retrieval.retriever import retrieve_context
from app.core.config import settings

async def ask_question(
    ai: AIProvider,
    kb_id: str,
    question: str,
    history: List[Dict[str, str]] | None = None,
    top_k: int = settings.CHAT_DEFAULT_TOP_K,
    temperature: float = settings.CHAT_DEFAULT_TEMPERATURE,
    max_tokens: int = settings.CHAT_DEFAULT_MAX_TOKENS,
) -> Tuple[str, List[dict]]:

    contexts, sources = await retrieve_context(ai, kb_id, question, top_k)

    messages = build_rag_messages(
        question=question,
        contexts=contexts,
        history=history or [],
    )

    result: ChatResult = await ai.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return result.text or "AI response is empty.", sources


async def stream_answer(
    ai: AIProvider,
    kb_id: str,
    question: str,
    history: List[Dict[str, str]] | None = None,
    top_k: int = 5,
) -> AsyncIterator[str]:

    contexts, _ = await retrieve_context(ai, kb_id, question, top_k)

    messages = build_rag_messages(
        question=question,
        contexts=contexts,
        history=history or [],
    )

    async for token in ai.stream_chat(messages):
        yield token