from qdrant_client import AsyncQdrantClient

from config.settings import settings


class Qdrant():
    def __init__(self):
        pass


    async def upsert_points(self, collection_name: str, points: list):
        qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)

        await qdrant.upsert(
            collection_name=collection_name,
            points=points
        )
