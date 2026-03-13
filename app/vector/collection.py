from qdrant_client.models import VectorParams, Distance
from app.core.config import settings
from app.vector.client import client
from app.vector.collections import get_collection_name

DISTANCE_MAP = {
    "cosine": Distance.COSINE,
    "dot": Distance.DOT,
    "euclid": Distance.EUCLID,
}


async def ensure_collection():
    collection = get_collection_name()
    collections = await client.get_collections()
    existing = [c.name for c in collections.collections]

    if collection in existing:
        return

    await client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(
            size=settings.EMBEDDING_DIM,
            distance=DISTANCE_MAP[settings.VECTOR_DISTANCE],
        ),
    )
