from __future__ import annotations

import os
import signal
import time
from dataclasses import dataclass
from typing import Any, Dict
import requests

from sqlalchemy.ext.asyncio import AsyncSession
from app.clients.laravel import laravel_client, laravel_routes

from app.core.config import settings

from app.db.session import AsyncSessionLocal
from app.providers.ai_factory import get_ai_provider
from app.providers.ai_provider import AIProvider


from app.services.chunking_service import ChunkingService
from app.services.loaders.dispatcher import load_pages_by_ext
from app.queue.redis_streams import RedisStreamsClient
from app.services.storage import S3Fetcher, S3Ref


STREAM = settings.AI_STREAM_NAME
GROUP = settings.AI_STREAM_GROUP
CONSUMER = settings.AI_STREAM_CONSUMER
DLQ_STREAM = settings.AI_DLQ_STREAM

REDIS_URL = settings.REDIS_URL
S3_REGION = settings.AWS_DEFAULT_REGION

MAX_ATTEMPTS = settings.AI_JOB_MAX_ATTEMPTS
RECLAIM_EVERY_SEC = settings.AI_RECLAIM_EVERY_SEC
MIN_IDLE_MS = settings.AI_RECLAIM_MIN_IDLE_MS

async def send_webhook(payload: dict):
    await laravel_client.post(laravel_routes.FILE_OPERATIONS_WEBHOOK, json=payload)

@dataclass(frozen=True)
class IngestJob:
    job_id: int
    kb_id: str
    file_id: int
    bucket: str
    key: str
    force_reprocess: bool = False
    attempt: int = 1


def _parse_job(fields: Dict[str, Any]) -> IngestJob:
    """
    We expect Backend to send the fields as strings.
    If a field contains JSON, we parse it using json.loads.
    """
    def get(name: str, default: Any = None) -> Any:
        return fields.get(name, default)

    job_id = int(get("operation_id"))
    kb_id = str(get("kb_id"))
    file_id = int(get("file_id"))
    bucket = str(get("s3_bucket"))
    key = str(get("s3_key"))
    force_reprocess = str(get("force_reprocess", "false")).lower() in {"1", "true", "yes"}
    attempt = int(get("attempt", "1"))

    return IngestJob(
        job_id=job_id,
        kb_id=kb_id,
        file_id=file_id,
        bucket=bucket,
        key=key,
        force_reprocess=force_reprocess,
        attempt=attempt,
    )



_shutdown = False
def _handle_sig(*_args):
    global _shutdown
    _shutdown = True


async def _run_one(job: IngestJob, *, db: AsyncSession, ai: AIProvider, s3: S3Fetcher) -> Dict[str, Any]:
    # 1) download
    local_path = s3.download_to_tmp(S3Ref(bucket=job.bucket, key=job.key))
    try:
        # 2) pages via loader
        ext = os.path.splitext(job.key)[1].lower().lstrip(".")
        pages = load_pages_by_ext(local_path, ext=ext)

        svc = ChunkingService(chunking_version="v1")
        res = await svc.process_file_pages(
            db=db,
            ai=ai,
            kb_id=job.kb_id,
            file_id=job.file_id,
            pages=pages,
            force_reprocess=job.force_reprocess,
        )
        return res
    finally:
        try:
            os.remove(local_path)
        except Exception:
            pass


async def main():

    global _shutdown

    signal.signal(signal.SIGTERM, _handle_sig)
    signal.signal(signal.SIGINT, _handle_sig)

    rs = RedisStreamsClient(redis_url=REDIS_URL)
    await rs.wait_until_ready()
    await rs.ensure_group(stream=STREAM, group=GROUP)

    s3 = S3Fetcher(region_name=S3_REGION)

    ai = get_ai_provider()

    last_reclaim = 0.0

    while not _shutdown:
        # reclaim stuck pending
        now = time.time()
        if now - last_reclaim >= RECLAIM_EVERY_SEC:
            last_reclaim = now
            try:
                claimed = await rs.claim_stuck(
                    stream=STREAM,
                    group=GROUP,
                    consumer=CONSUMER,
                    min_idle_ms=MIN_IDLE_MS,
                    count=20,
                )
                for m in claimed:
                    await _handle_message(rs, m.stream, m.msg_id, m.data, ai=ai, s3=s3)
            except Exception:
                pass

        # read new messages
        msgs = await rs.read_group(stream=STREAM, group=GROUP, consumer=CONSUMER, count=10, block_ms=5000)
        for m in msgs:
            await _handle_message(rs, m.stream, m.msg_id, m.data, ai=ai, s3=s3)

    # graceful exit
    return


async def _handle_message(
    rs: RedisStreamsClient,
    stream: str,
    msg_id: str,
    fields: Dict[str, Any],
    *,
    ai: AIProvider,
    s3: S3Fetcher,
) -> None:
    # parse
    try:
        job = _parse_job(fields)
    except Exception as e:
        await rs.add(stream=DLQ_STREAM, data={"reason": "bad_payload", "error": str(e), "original": fields}, maxlen=10000)
        await rs.ack(stream=stream, group=GROUP, msg_id=msg_id)
        return

    from uuid import UUID
    try:
        UUID(job.kb_id)  # Just validate, don't convert
    except Exception as e:
        await rs.add(stream=DLQ_STREAM, data={"reason": "bad_kb_id", "error": str(e), "job": fields}, maxlen=10000)
        await rs.ack(stream=stream, group=GROUP, msg_id=msg_id)
        return

    # job.kb_id is already a valid UUID string, no need to convert

    if job.attempt == 1:
        try:
            await send_webhook({
                "operation_id": job.job_id,
                "status": "processing"
            })
        except Exception as e:
            pass

    # run
    try:
        async with AsyncSessionLocal() as db:
            await _run_one(job, db=db, ai=ai, s3=s3)

        try:
            await send_webhook({
                "operation_id": job.job_id,
                "status": "processed"
            })
        except Exception as e:
            pass
        await rs.ack(stream=stream, group=GROUP, msg_id=msg_id)
        return

    except Exception as e:
        error_type = type(e).__name__
        attempt = job.attempt
        if attempt >= MAX_ATTEMPTS:
            await rs.add(
                stream=DLQ_STREAM,
                data={
                    "reason": "max_attempts",
                    "attempt": attempt,
                    "error": str(e),
                    "error_type": error_type,
                    "job": fields,
                },
                maxlen=10000,
            )
            try:
                await send_webhook({
                    "operation_id": job.job_id,
                    "status": "failed"
                })
            except Exception as e:
                pass
            await rs.ack(stream=stream, group=GROUP, msg_id=msg_id)
            return

        # requeue
        new_fields = dict(fields)
        new_fields["attempt"] = str(attempt + 1)
        new_fields["last_error"] = str(e)
        await rs.add(stream=STREAM, data=new_fields, maxlen=200000)
        await rs.ack(stream=stream, group=GROUP, msg_id=msg_id)
        return


if __name__ == "__main__":
    print("Worker loop alive")

    import asyncio
    asyncio.run(main())
