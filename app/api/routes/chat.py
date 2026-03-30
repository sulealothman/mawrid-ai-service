from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps.providers import get_ai_provider_dep
from app.api.deps.ws_auth import authenticate_websocket
from app.application.chat.session import handle_generation
from app.api.schemas.chat import WSMessageSendPayload, WSCancelPayload


router = APIRouter()


@router.websocket("/v1/ws/chat")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        token_payload = await authenticate_websocket(websocket)
    except Exception as e:
        await websocket.close(code=1008, reason=str(getattr(e, "reason", "Unauthorized")))
        return

    ai = get_ai_provider_dep()
    active_tasks: dict[str, asyncio.Task] = {}

    await websocket.send_json({
        "type": "ready",
        "chat_id": token_payload.get("chat_id"),
    })

    try:
        while True:
            incoming = await websocket.receive_json()
            event_type = incoming.get("type")

            if event_type == "message.send":
                payload = WSMessageSendPayload.model_validate(incoming)

                if str(payload.chat_id) != str(token_payload.get("chat_id")):
                    await websocket.send_json({
                        "type": "error",
                        "request_id": payload.request_id,
                        "message": "chat_id mismatch",
                    })
                    continue

                if str(payload.kb_id) != str(token_payload.get("kb_id")):
                    await websocket.send_json({
                        "type": "error",
                        "request_id": payload.request_id,
                        "message": "kb_id mismatch",
                    })
                    continue

                task = asyncio.create_task(
                    handle_generation(
                        websocket=websocket,
                        ai=ai,
                        request_id=payload.request_id,
                        chat_id=str(payload.chat_id),
                        kb_id=str(payload.kb_id),
                        message=payload.message,
                        parent_id=payload.parent_id,
                    )
                )
                active_tasks[payload.request_id] = task

            elif event_type == "generation.cancel":
                payload = WSCancelPayload.model_validate(incoming)
                task = active_tasks.get(payload.request_id)

                if task and not task.done():
                    task.cancel()

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unsupported event type",
                })

    except WebSocketDisconnect:
        for task in active_tasks.values():
            if not task.done():
                task.cancel()
        with suppress(Exception):
            await ai.close()
    finally:
        with suppress(Exception):
            await ai.close()


