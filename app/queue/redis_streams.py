from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis
from redis.exceptions import ResponseError
from redis.exceptions import RedisError
import asyncio


@dataclass(frozen=True)
class StreamMessage:
    stream: str
    msg_id: str
    data: Dict[str, Any]


class RedisStreamsClient:
    def __init__(self, *, redis_url: str):
        self.r: Redis = Redis.from_url(redis_url, decode_responses=True)

    async def wait_until_ready(self, retry_delay: int = 10):
        while True:
            try:
                await self.r.ping()
                return
            except RedisError:
                print(f"Redis not ready, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

    async def ensure_group(self, *, stream: str, group: str) -> None:
        try:
            await self.r.xgroup_create(stream, group, id="0", mkstream=True)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def read_group(
        self,
        *,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 5000,
        read_pending: bool = False,
    ) -> List[StreamMessage]:

        stream_id = "0" if read_pending else ">"

        resp = await self.r.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: stream_id},
            count=count,
            block=block_ms,
        )

        out: List[StreamMessage] = []
        for st, msgs in resp:
            for msg_id, fields in msgs:
                out.append(StreamMessage(stream=st, msg_id=msg_id, data=fields))
        return out

    async def ack(self, *, stream: str, group: str, msg_id: str) -> None:
        await self.r.xack(stream, group, msg_id)

    async def delete(self, *, stream: str, msg_id: str) -> None:
        await self.r.xdel(stream, msg_id)

    async def add(
        self,
        *,
        stream: str,
        data: Dict[str, Any],
        maxlen: Optional[int] = None,
    ) -> str:

        kwargs = {}
        if maxlen is not None:
            kwargs["maxlen"] = maxlen
            kwargs["approximate"] = True

        flat = {
            k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
            for k, v in data.items()
        }

        return await self.r.xadd(stream, flat, **kwargs)

    async def claim_stuck(
        self,
        *,
        stream: str,
        group: str,
        consumer: str,
        min_idle_ms: int,
        count: int = 20,
    ) -> List[StreamMessage]:

        pending = await self.r.xpending_range(
            stream,
            group,
            min="-",
            max="+",
            count=count,
        )

        ids = [
            p["message_id"]
            for p in pending
            if p.get("time_since_delivered", 0) >= min_idle_ms
        ]

        if not ids:
            return []

        claimed = await self.r.xclaim(
            stream,
            group,
            consumer,
            min_idle_ms,
            ids,
        )

        out: List[StreamMessage] = []
        for msg_id, fields in claimed:
            out.append(StreamMessage(stream=stream, msg_id=msg_id, data=fields))
        return out
