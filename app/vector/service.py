from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.vector.client import client
from app.core.config import settings

from app.vector.collections import get_collection_name

COLLECTION_NAME = get_collection_name()


class QdrantService:

    @staticmethod
    async def upsert_vectors(chunks_with_vectors):
        points = [
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "chunk_id": chunk_id,
                    "kb_id": str(kb_id),
                    "file_id": file_id,
                },
            )
            for chunk_id, vector, kb_id, file_id in chunks_with_vectors
        ]

        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

    @staticmethod
    async def search(vector, kb_id, limit=5):
        result = await client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=limit,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=str(kb_id))
                    )
                ]
            ),
        )

        return [point.id for point in result.points]

    @staticmethod
    async def delete_by_file(file_id):
        await client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(value=file_id)
                    )
                ]
            ),
        )

    @staticmethod
    async def delete_by_kb(kb_id):
        await client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=str(kb_id))
                    )
                ]
            ),
        )
