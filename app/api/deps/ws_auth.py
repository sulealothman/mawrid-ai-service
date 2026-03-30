from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import WebSocket, WebSocketException, status

from app.core.config import settings


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def verify_ws_token(token: str) -> dict[str, Any]:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token format")

    expected_signature = hmac.new(
        settings.AI_WS_TOKEN_SECRET.encode(),
        payload_part.encode(),
        hashlib.sha256,
    ).digest()

    try:
        given_signature = _base64url_decode(signature_part)
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token signature")

    if not hmac.compare_digest(expected_signature, given_signature):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Token signature mismatch")

    try:
        payload = json.loads(_base64url_decode(payload_part))
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")

    now = int(time.time())
    exp = int(payload.get("exp", 0))

    if exp < now:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Token expired")

    return payload


async def authenticate_websocket(websocket: WebSocket) -> dict[str, Any]:
    token = websocket.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    return verify_ws_token(token)