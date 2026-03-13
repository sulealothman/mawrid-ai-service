import re
from app.core.config import settings
from app.vector.client import client

def normalize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).lower()

def get_collection_name() -> str:
    model = normalize(settings.AI_EMBED_MODEL)
    dim = settings.EMBEDDING_DIM
    base = settings.QDRANT_COLLECTION
    return f"{base}_{model}_{dim}"

async def get_other_collections(current: str):
    collections = await client.get_collections()
    return [
        c.name
        for c in collections.collections
        if c.name.startswith(settings.QDRANT_COLLECTION)
        and c.name != current
    ]