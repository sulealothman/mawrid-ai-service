from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    request_id: str
    kb_id: UUID
    query: str
    messages: List[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    sources: List[dict]
    usage: Optional[dict] = None
