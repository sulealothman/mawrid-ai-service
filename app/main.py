from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.api.routes.title_generate import router as title_router
from app.core.config import settings
from app.vector import ensure_collection


app = FastAPI(title=settings.APP_TITLE)

@app.on_event("startup")
async def startup():
    await ensure_collection()

app.include_router(chat_router)
app.include_router(title_router)



@app.get("/")
async def root():
    return {"status": "running", "service": "ai-doc-qa"}
