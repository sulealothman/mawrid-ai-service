from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.providers.ai_factory import get_ai_provider
from app.prompts.base import PromptBuilder
from app.core.config import settings


router = APIRouter(prefix="/v1")


# ------------------------
# Request / Response Models
# ------------------------

class TitleGenerationConfig(BaseModel):
    temperature: float = 0.1
    max_tokens: int = 20


class Message(BaseModel):
    role: str
    content: str


class TitleRequest(BaseModel):
    request_id: str
    messages: list[Message]
    generation: TitleGenerationConfig = Field(default_factory=TitleGenerationConfig)


class TitleResponse(BaseModel):
    request_id: str
    title: str
    usage: Optional[dict] = None


@router.post("/generate-title", response_model=TitleResponse)
async def generate_title(
    req: TitleRequest,
    x_internal_key: str = Header(...)
):

    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    ai = get_ai_provider()


    messages = PromptBuilder.build_title_from_history(
        history=[m.model_dump() for m in req.messages if m.content.strip()]
    )

    response = await ai.chat(
        messages=messages,
        temperature=req.generation.temperature,
        max_tokens=req.generation.max_tokens,
    )

    title = (response.text or "").strip().replace('"', '')

    return TitleResponse(
        request_id=req.request_id,
        title=title,
        usage=None,
    )
