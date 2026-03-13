from __future__ import annotations

from typing import AsyncIterator, List, Dict, Tuple

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.providers.ai_provider import AIProvider
from app.providers.schemas import ChatResult
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.chunk import Chunk
from app.vector.client import client


from app.prompts.rag_prompt import RAG_PROMPT

from app.vector.collections import get_collection_name, get_other_collections
from app.vector.service import QdrantService

COLLECTION_NAME = get_collection_name()


MAX_CONTEXT_CHARS = 12000
DEFAULT_MAX_TOKENS = 800
DEFAULT_TEMPERATURE = 0.2


async def ask_question(
    ai: AIProvider,
    kb_id: str,
    question: str,
    history: List[Dict[str, str]] | None = None,
    top_k: int = 5,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Tuple[str, List[dict]]:

    contexts, sources = await _retrieve_context(ai, kb_id, question, top_k)

    messages = _build_messages(
        question=question,
        contexts=contexts,
        history=history or [],
    )

    result: ChatResult = await ai.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return result.text, sources


async def stream_answer(
    ai: AIProvider,
    kb_id: str,
    question: str,
    history: List[Dict[str, str]] | None = None,
    top_k: int = 5,
) -> AsyncIterator[str]:

    contexts, _ = await _retrieve_context(ai, kb_id, question, top_k)

    messages = _build_messages(
        question=question,
        contexts=contexts,
        history=history or [],
    )

    async for token in ai.stream_chat(messages):
        yield token


# async def _retrieve_context(
#     ai: AIProvider,
#     kb_id: str,
#     question: str,
#     top_k: int,
# ) -> Tuple[List[str], List[dict]]:

#     emb = await ai.embed([question])
#     query_vector = emb.vectors[0]

#     filt = Filter(
#         must=[
#             FieldCondition(
#                 key="kb_id",
#                 match=MatchValue(value=str(kb_id)),
#             )
#         ]
#     )

#     try:
#         res = await client.query_points(
#             collection_name=COLLECTION_NAME,
#             query=query_vector,
#             limit=top_k,
#             query_filter=filt,
#         )
#     except TypeError:
#         res = await client.query_points(
#             collection_name=COLLECTION_NAME,
#             query=query_vector,
#             limit=top_k,
#             filter=filt,
#         )

#     points = getattr(res, "points", None) or []
#     if not points:
#         return [], []

#     chunk_ids: List[int] = []
#     scored: List[Tuple[int, float | None]] = []

#     for p in points:
#         payload = p.payload or {}
#         cid = payload.get("chunk_id")
#         if cid is None:
#             continue
#         score = getattr(p, "score", None)
#         chunk_ids.append(int(cid))
#         scored.append((int(cid), score))

#     if not chunk_ids:
#         return [], []

#     async with AsyncSessionLocal() as session:
#         result = await session.execute(
#             select(Chunk.id, Chunk.text, Chunk.page, Chunk.file_id)
#             .where(Chunk.id.in_(chunk_ids))
#             .where(Chunk.kb_id == kb_id)
#         )
#         rows = result.all()

#     row_map = {r.id: r for r in rows}

#     contexts: List[str] = []
#     sources: List[dict] = []
#     total_chars = 0

#     for cid, score in scored:
#         r = row_map.get(cid)
#         if not r:
#             continue

#         text = r.text
#         page = r.page
#         file_id = r.file_id

#         formatted = f"(Page {page}) {text}" if page is not None else text

#         if total_chars + len(formatted) > MAX_CONTEXT_CHARS:
#             break

#         contexts.append(formatted)
#         total_chars += len(formatted)

#         sources.append(
#             {
#                 "file_id": int(file_id) if file_id is not None else None,
#                 "page": int(page) if page is not None else None,
#                 "chunk_id": int(cid),
#                 "score_vector": score,
#             }
#         )

#     return contexts, sources


async def _retrieve_context(
    ai: AIProvider,
    kb_id: str,
    question: str,
    top_k: int,
) -> Tuple[List[str], List[dict]]:

    collection = get_collection_name()

    emb = await ai.embed([question])
    query_vector = emb.vectors[0]

    filt = Filter(
        must=[
            FieldCondition(
                key="kb_id",
                match=MatchValue(value=str(kb_id)),
            )
        ]
    )

    # -----------------------
    # 1️⃣ Vector search
    # -----------------------

    res = await client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k,
        query_filter=filt,
    )

    points = getattr(res, "points", None) or []

    # -----------------------
    # 2️⃣ Lazy fallback
    # -----------------------

    if not points:

        async with AsyncSessionLocal() as session:

            result = await session.execute(
                select(
                    Chunk.id,
                    Chunk.text,
                    Chunk.page,
                    Chunk.file_id,
                )
                .where(Chunk.kb_id == kb_id)
                .where(Chunk.text.ilike(f"%{question}%"))
                .limit(20)
            )

            rows = result.all()

        if not rows:
            return [], []

        texts = [r.text for r in rows]

        emb = await ai.embed(texts)

        payloads = [
            (rows[i].id, emb.vectors[i], kb_id, rows[i].file_id)
            for i in range(len(rows))
        ]

        # store vectors in new collection
        await QdrantService.upsert_vectors(payloads)

        # search again after re-embedding
        res = await client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            query_filter=filt,
        )

        points = getattr(res, "points", None) or []

        if not points:
            return [], []

    # -----------------------
    # 3️⃣ Extract chunk ids
    # -----------------------

    chunk_ids: List[int] = []
    scored: List[Tuple[int, float | None]] = []

    for p in points:

        payload = p.payload or {}
        cid = payload.get("chunk_id")

        if cid is None:
            continue

        score = getattr(p, "score", None)

        chunk_ids.append(int(cid))
        scored.append((int(cid), score))

    if not chunk_ids:
        return [], []

    # -----------------------
    # 4️⃣ Fetch chunk text
    # -----------------------

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(
                Chunk.id,
                Chunk.text,
                Chunk.page,
                Chunk.file_id,
            )
            .where(Chunk.id.in_(chunk_ids))
            .where(Chunk.kb_id == kb_id)
        )

        rows = result.all()

    row_map = {r.id: r for r in rows}

    contexts: List[str] = []
    sources: List[dict] = []

    total_chars = 0

    for cid, score in scored:

        r = row_map.get(cid)
        if not r:
            continue

        text = r.text
        page = r.page
        file_id = r.file_id

        formatted = f"(Page {page}) {text}" if page is not None else text

        if total_chars + len(formatted) > MAX_CONTEXT_CHARS:
            break

        contexts.append(formatted)
        total_chars += len(formatted)

        sources.append(
            {
                "file_id": int(file_id) if file_id is not None else None,
                "page": int(page) if page is not None else None,
                "chunk_id": int(cid),
                "score_vector": score,
            }
        )

    return contexts, sources

def _build_messages(
    question: str,
    contexts: List[str],
    history: List[Dict[str, str]],
) -> List[Dict[str, str]]:

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": RAG_PROMPT}
    ]

    trimmed_history = history[-10:] if history else []

    for m in trimmed_history:
        if m.get("role") in ("user", "assistant"):
            messages.append(
                {
                    "role": m["role"],
                    "content": m["content"],
                }
            )

    if contexts:
        context_text = "\n\n".join(contexts)

        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{context_text}",
            }
        )

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    return messages
