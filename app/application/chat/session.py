import asyncio
from typing import Any
from fastapi import WebSocket

from app.application.chat.finalize import finalize_chat
from app.application.chat.service import build_stream_answer

async def handle_generation(
    *,
    websocket: WebSocket,
    ai,
    request_id: str,
    chat_id: str,
    kb_id: str,
    message: str,
    parent_id: int | None,
) -> None:
    full_answer = ""
    sources: list[dict[str, Any]] = []

    try:
        await websocket.send_json({
            "type": "ack",
            "request_id": request_id,
        })

        await websocket.send_json({
            "type": "status",
            "request_id": request_id,
            "status": "retrieving",
        })

        token_stream, sources = await build_stream_answer(ai=ai, kb_id=kb_id, question=message)

        await websocket.send_json({
            "type": "status",
            "request_id": request_id,
            "status": "streaming",
        })

        async for token in token_stream:
            full_answer += token

            await websocket.send_json({
                "type": "delta",
                "request_id": request_id,
                "content": token,
            })

        persisted = await finalize_chat(
            chat_id=chat_id,
            message=message,
            answer=full_answer,
            status="completed",
            status_message=None,
            parent_id=parent_id,
            sources=sources,
            usage=None,
        )
        await websocket.send_json({
            "type": "done",
            "request_id": request_id,
            "data": persisted,
        })

    except asyncio.CancelledError:
        persisted = await finalize_chat(
            chat_id=chat_id,
            message=message,
            answer=full_answer,
            status="cancelled",
            status_message="user cancelled",
            parent_id=parent_id,
            sources=sources,
            usage=None,
        )

        await websocket.send_json({
            "type": "cancelled",
            "request_id": request_id,
            "data": persisted,
        })

        raise

    except Exception as e:
        persisted = await finalize_chat(
            chat_id=chat_id,
            message=message,
            answer=full_answer or "",
            status="failed",
            status_message=str(e),
            parent_id=parent_id,
            sources=sources,
            usage=None,
        )
        await websocket.send_json({
            "type": "error",
            "request_id": request_id,
            "data": persisted,
        })