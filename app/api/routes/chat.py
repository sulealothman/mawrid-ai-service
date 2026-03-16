from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps.auth import verify_internal_api_key
from app.api.deps.providers import get_ai_provider_dep
from app.application.chat.service import ask_question
from app.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(verify_internal_api_key)],
)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    ai = Depends(get_ai_provider_dep)
):

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
