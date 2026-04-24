from qdrant_client import QdrantClient

from app.core.config import config


class Qdrant():
    def __init__(self):
        self.qdrant = QdrantClient(url=config.QDRANT_HOST)


    def upsert_points(self, collection_name: str, points: list):
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )


    def find_points(self, collection_name: str, query: list, limit: int = 5):
        response = self.qdrant.query_points(
            collection_name=collection_name,
            query=query,
            limit=limit
        )

        return response.points