from qdrant_client import AsyncQdrantClient

from config.settings import settings


class Qdrant():
    def __init__(self):
        self.qdrant = AsyncQdrantClient(url=settings.QDRANT_HOST)


    async def upsert_points(self, collection_name: str, points: list):
        await self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )


    async def find_points(self, collection_name: str, query: list, limit: int = 5):
        response = await self.qdrant.query_points(
            collection_name=collection_name,
            query=query,
            limit=limit
        )

        return response.points
