from fastapi import Depends
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO

from app.core.dependencies.common import get_embedding_model, get_qdrant, get_yolo_model
from app.infrastructure.vectordb.qdrant import Qdrant
from app.services.fruit.point import FruitPointService
from app.services.fruit.search import FruitSearchService


def get_fruit_point_service(
    qdrant: Qdrant = Depends(get_qdrant),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    yolo_model: YOLO = Depends(get_yolo_model)
) -> FruitPointService:
    return FruitPointService(qdrant, embedding_model, yolo_model)


def get_fruit_search_service(
    fruit_point_service: FruitSearchService = Depends(get_fruit_point_service)
) -> FruitSearchService:
    return FruitSearchService(fruit_point_service)