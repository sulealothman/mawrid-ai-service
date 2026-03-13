from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from app.providers.ai_factory import get_ai_provider
from app.services.rag import ask_question
from app.core.config import settings


router = APIRouter(prefix="/v1")


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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    x_internal_key: str = Header(...)
):

    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    ai = get_ai_provider()

    answer, sources = await ask_question(
        ai=ai,
        kb_id=str(req.kb_id),
        question=req.query,
        history=[m.model_dump() for m in req.messages],
        top_k=req.retrieval.top_k,
        temperature=req.generation.temperature,
        max_tokens=req.generation.max_tokens,
    )

    return ChatResponse(
        request_id=req.request_id,
        answer=answer,
        sources=sources,
        usage=None,
    )
