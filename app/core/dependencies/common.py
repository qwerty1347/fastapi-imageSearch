from functools import lru_cache
from fastapi import Depends
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO

from app.core.config import config
from app.infrastructure.vectordb.qdrant import Qdrant
from config.embedding_model import EmbeddingModel


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=config.QDRANT_HOST)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EmbeddingModel.MODELS['hugging_face']['clip']['ViT-L-14']['name'])


@lru_cache
def get_yolo_model() -> YOLO:
    return YOLO("yolov8n-oiv7.pt")


def get_qdrant(client: QdrantClient = Depends(get_qdrant_client)) -> Qdrant:
    return Qdrant(client)