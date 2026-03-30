from __future__ import annotations

from typing import Any
from app.clients.laravel import laravel_client, laravel_routes

async def finalize_chat(
    *,
    chat_id: str,
    message: str,
    answer: str | None,
    status: str,
    status_message: str | None = None,
    parent_id: int | None = None,
    sources: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
) -> None:
    payload = {
        "chat_id": chat_id,
        "message": message,
        "answer": answer,
        "status": status,
        "status_message": status_message,
        "parent_id": parent_id,
        "sources": sources or [],
        "usage": usage,
    }

    response = await laravel_client.post(laravel_routes.CHAT_FINALIZE, json=payload)
    return response.json()['data']