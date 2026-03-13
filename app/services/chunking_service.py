from __future__ import annotations

from uuid import UUID as PyUUID
from typing import Iterable

import tiktoken
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.enum import ChunkingStatus
from app.db.models.chunk import Chunk
from app.db.models.chunking_job import ChunkingJob
from app.providers.ai_provider import AIProvider
from app.services.chunking import chunk_text
from app.services.types import Page
from app.vector.service import QdrantService


class ChunkingService:
    def __init__(self, chunking_version: str = "v1"):
        self.chunking_version = chunking_version
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text or ""))

    async def process_file_pages(
        self,
        *,
        db: AsyncSession,
        ai: AIProvider,
        kb_id: PyUUID,
        file_id: int,
        pages: Iterable[Page],
        force_reprocess: bool = False,
        insert_batch_size: int = 500,
        embed_batch_size: int = 64,
    ) -> dict:

        job = await self._get_or_create_job(db=db, kb_id=kb_id, file_id=file_id)

        if job.status == ChunkingStatus.canceled:
            return {"status": "canceled", "file_id": file_id, "kb_id": str(kb_id)}

        if job.status == ChunkingStatus.processed and not force_reprocess:
            return {"status": "already_processed", "file_id": file_id, "kb_id": str(kb_id)}

        job.status = ChunkingStatus.processing
        job.error_message = None
        job.started_at = func.now()
        await db.commit()

        try:
            if force_reprocess:
                await self._delete_existing(db=db, kb_id=kb_id, file_id=file_id)

            rows: list[dict] = []

            async def flush_rows():
                nonlocal rows
                if not rows:
                    return

                stmt = pg_insert(Chunk).values(rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=[
                        Chunk.kb_id,
                        Chunk.file_id,
                        Chunk.page,
                        Chunk.chunk_index,
                        Chunk.chunking_version,
                    ]
                )

                await db.execute(stmt)
                await db.commit()
                rows = []

            for page in pages:
                page_text = (page.text or "").strip()
                if not page_text:
                    continue

                chunks = chunk_text(page_text)

                for idx, c in enumerate(chunks):
                    txt = (c.get("text") or "").strip()
                    if not txt:
                        continue

                    rows.append(
                        {
                            "file_id": file_id,
                            "kb_id": kb_id,
                            "page": int(page.page),
                            "chunk_index": int(idx),
                            "text": txt,
                            "token_count": self._count_tokens(txt),
                            "chunking_version": self.chunking_version,
                            "vectorized_at": None,
                        }
                    )

                    if len(rows) >= insert_batch_size:
                        await flush_rows()

            await flush_rows()

            stmt = select(Chunk).where(
                Chunk.kb_id == kb_id,
                Chunk.file_id == file_id,
                Chunk.vectorized_at.is_(None),
            )

            result = await db.execute(stmt)
            pending_chunks = result.scalars().all()

            total_vectorized = 0
            i = 0

            while i < len(pending_chunks):
                batch = pending_chunks[i : i + embed_batch_size]
                texts = [c.text for c in batch]

                emb = await ai.embed(texts)
                vectors = emb.vectors
                n = min(len(batch), len(vectors))

                payloads = [
                    (batch[j].id, vectors[j], kb_id, file_id)
                    for j in range(n)
                ]

                await QdrantService.upsert_vectors(payloads)

                for j in range(n):
                    batch[j].vectorized_at = func.now()

                await db.commit()

                total_vectorized += n
                i += embed_batch_size

            job.status = ChunkingStatus.processed
            job.finished_at = func.now()
            await db.commit()

            return {
                "status": "processed",
                "file_id": file_id,
                "kb_id": str(kb_id),
                "chunks_vectorized": total_vectorized,
            }

        except Exception as e:
            job.retry_count = (job.retry_count or 0) + 1
            job.status = ChunkingStatus.failed
            job.error_message = str(e)
            job.finished_at = func.now()
            await db.commit()
            raise

    async def _get_or_create_job(self, *, db: AsyncSession, kb_id: PyUUID, file_id: int) -> ChunkingJob:
        stmt = select(ChunkingJob).where(
            ChunkingJob.kb_id == kb_id,
            ChunkingJob.file_id == file_id,
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if job:
            return job

        job = ChunkingJob(
            kb_id=kb_id,
            file_id=file_id,
            status=ChunkingStatus.queued,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def _delete_existing(self, *, db: AsyncSession, kb_id: PyUUID, file_id: int) -> None:
        await QdrantService.delete_by_file(file_id=file_id)

        await db.execute(
            delete(Chunk).where(
                Chunk.kb_id == kb_id,
                Chunk.file_id == file_id,
            )
        )
        await db.commit()
