from __future__ import annotations

from app.domain.prompts.message_builder import build_rag_messages
from app.domain.retrieval.retriever import retrieve_context
from app.core.config import settings

async def build_stream_answer(*, ai, kb_id: str, question: str):

    contexts, sources = await retrieve_context(ai, kb_id, question, settings.CHAT_DEFAULT_TOP_K)

    messages = build_rag_messages(
        question=question,
        contexts=contexts,
        history=[],
    )

    async def generator():
        async for token in ai.stream_chat(
            messages=messages,
            temperature=settings.CHAT_DEFAULT_TEMPERATURE,
            max_tokens=settings.CHAT_DEFAULT_MAX_TOKENS,
        ):
            yield token

    return generator(), sources