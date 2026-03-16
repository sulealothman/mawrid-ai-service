from __future__ import annotations

from typing import List, Tuple

from qdrant_client.models import Filter, FieldCondition, MatchValue
from sqlalchemy import select

from app.db.models.chunk import Chunk
from app.db.session import AsyncSessionLocal
from app.providers.ai_provider import AIProvider
from app.vector.client import client
from app.vector.collections import get_collection_name
from app.vector.service import QdrantService

MAX_CONTEXT_CHARS = 12000

async def retrieve_context(
    ai: AIProvider,
    kb_id: str,
    question: str,
    top_k: int,
) -> Tuple[List[str], List[dict]]:

    collection = get_collection_name()
    query_vector = await _embed_question(ai, question)

    points = await _search_vector_points(
        collection=collection,
        kb_id=kb_id,
        query_vector=query_vector,
        top_k=top_k,
     )

    if not points:
        points = await _fallback_reindex_and_search(
            ai=ai,
            kb_id=kb_id,
            question=question,
            query_vector=query_vector,
            collection=collection,
            top_k=top_k,
         )

        if not points:
            return [], []
        
    scored = _extract_scored_chunk_ids(points)
    if not scored:
        return [], []
    
    chunk_ids = [cid for cid, _ in scored]
    rows = await _load_chunks(kb_id, chunk_ids)

    return _assemble_contexts(rows, scored)
    


async def _embed_question(ai: AIProvider, question: str) -> list[float]:
    emb = await ai.embed([question])
    return emb.vectors[0]


async def _search_vector_points(
    collection: str,
    kb_id: str,
    query_vector: list[float],
    top_k: int,
):
    filt = Filter(
        must=[
            FieldCondition(
                key="kb_id",
                match=MatchValue(value=str(kb_id)),
            )
        ]
    )

    res = await client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k,
        query_filter=filt,
    )

    return getattr(res, "points", None) or []


async def _fallback_reindex_and_search(
    ai: AIProvider,
    kb_id: str,
    question: str,
    query_vector: list[float],
    collection: str,
    top_k: int,
):
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

        await QdrantService.upsert_vectors(payloads)

        return await _search_vector_points(
            collection=collection,
            kb_id=kb_id,
            query_vector=query_vector,
            top_k=top_k,
        )

def _extract_scored_chunk_ids(points) -> List[Tuple[int, float | None]]:
    scored: List[Tuple[int, float | None]] = []

    for p in points:
        payload = p.payload or {}
        cid = payload.get("chunk_id")
        if cid is None:
            continue
        score = getattr(p, "score", None)
        scored.append((int(cid), score))

    return scored

async def _load_chunks(kb_id: str, chunk_ids: List[int]):
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

        return result.all()
    
def _assemble_contexts(rows, scored: List[Tuple[int, float | None]]):
    row_map = {r.id: r for r in rows}

    contexts: List[str] = []
    sources: List[dict] = []

    total_chars = 0

    for cid, score in scored:

        row = row_map.get(cid)
        if not row:
            continue


        formatted = f"(Page {row.page}) {row.text}" if row.page is not None else row.text

        if total_chars + len(formatted) > MAX_CONTEXT_CHARS:
            break

        contexts.append(formatted)
        total_chars += len(formatted)

        sources.append(
            {
                "file_id": int(row.file_id) if row.file_id is not None else None,
                "page": int(row.page) if row.page is not None else None,
                "chunk_id": int(cid),
                "score_vector": score,
            }
        )

    return contexts, sources