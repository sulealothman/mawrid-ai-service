from fastapi import APIRouter, Depends
from app.api.deps.auth import verify_internal_api_key
from app.api.deps.providers import get_ai_provider_dep
from app.api.schemas.title import TitleRequest, TitleResponse
from app.application.title.service import generate_title

router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(verify_internal_api_key)],
)

@router.post("/generate-title", response_model=TitleResponse)
async def title(
    req: TitleRequest,
    ai = Depends(get_ai_provider_dep)
):
    
    title, usage = await generate_title(
        ai=ai,
        history=[m.model_dump() for m in req.messages],
        temperature=req.generation.temperature,
        max_tokens=req.generation.max_tokens,
    )

    return TitleResponse(
        request_id=req.request_id,
        title=title,
        usage=usage,
    )
