from fastapi import APIRouter, Depends
from app.api.deps.auth import verify_internal_api_key
from app.api.deps.providers import get_ai_provider_dep
from app.prompts.base import PromptBuilder
from app.api.schemas.title import TitleRequest, TitleResponse

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(verify_internal_api_key)],
)



@router.post("/generate-title", response_model=TitleResponse)
async def generate_title(
    req: TitleRequest,
    ai = Depends(get_ai_provider_dep)
):

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
