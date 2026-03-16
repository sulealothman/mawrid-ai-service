from fastapi import FastAPI
from app.core.config import settings
from app.vector import ensure_collection
from app.api.router import api_router

app = FastAPI(title=settings.APP_TITLE)

@app.on_event("startup")
async def startup():
    await ensure_collection()

app.include_router(api_router)



@app.get("/")
async def root():
    return {"status": "running", "service": "ai-doc-qa"}
