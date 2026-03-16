from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class Message(BaseModel):
    role: str
    content: str


class RetrievalConfig(BaseModel):
    top_k: int = 5


class GenerationConfig(BaseModel):
    temperature: float = 0.2
    max_tokens: int = 800


class ChatRequest(BaseModel):
    request_id: str
    kb_id: UUID
    query: str
    messages: List[Message] = Field(default_factory=list)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    sources: List[dict]
    usage: Optional[dict] = None
