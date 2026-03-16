from fastapi import APIRouter
from app.api.routes.chat import router as chat_router
from app.api.routes.title_generate import router as titles_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(titles_router)