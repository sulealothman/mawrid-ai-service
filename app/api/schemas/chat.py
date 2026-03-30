from __future__ import annotations

from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID

class WSMessageSendPayload(BaseModel):
    type: Literal["message.send"]
    request_id: str
    chat_id: UUID
    kb_id: UUID
    message: str
    parent_id: Optional[int] = None


class WSCancelPayload(BaseModel):
    type: Literal["generation.cancel"]
    request_id: str