from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ─────────── App ───────────
    APP_URL: str = "http://localhost"
    APP_TITLE: str = "Mawrid AI Service"
    APP_DESCRIPTION: str = "Mawrid is a smart RAG system to build knowledge bases, upload files, and chat with them using AI"

    # ─────────── AI Provider ───────────
    AI_PROVIDER: str = "openrouter"
    AI_API_KEY: str
    AI_BASE_URL: str

    AI_CHAT_MODEL: str
    AI_EMBED_MODEL: str
    EMBEDDING_DIM: int = Field(..., description="Embedding vector dimension")

    # ─────────── Chat Config ───────────
    CHAT_DEFAULT_TEMPERATURE: float = 0.2
    CHAT_DEFAULT_MAX_TOKENS: int = 4096
    CHAT_DEFAULT_TOP_K: int = 5

    # ─────────── Chunking Config ───────────
    CHUNK_MAX_TOKENS: int = 4096
    CHUNK_OVERLAP_TOKENS: int = 512
    CHUNK_ENCODING: str = "cl100k_base"

    # ─────────── Database ───────────
    DATABASE_URL: str
    DATABASE_URL_SYNC: str


    # ─────────── Qdrant ───────────
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "chunks"
    VECTOR_DISTANCE: str = "cosine"  # cosine | dot | euclid


    # ─────────── Internal API ───────────
    INTERNAL_API_KEY: str = "default_internal_key"

    LARAVEL_WEBHOOK_URL: str

    REDIS_URL: str

    # ─────────── AI Job Config ───────────
    AI_STREAM_NAME: str = "ai:jobs"
    AI_STREAM_GROUP: str = "ai-workers"
    AI_STREAM_CONSUMER: str = "worker-1"
    AI_DLQ_STREAM: str = "ai:jobs:dlq"

    AI_JOB_MAX_ATTEMPTS: int = 3
    AI_RECLAIM_EVERY_SEC: int = 20
    AI_RECLAIM_MIN_IDLE_MS: int = 120000


    # ─────────── S3 ───────────
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str
    AWS_ENDPOINT_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
