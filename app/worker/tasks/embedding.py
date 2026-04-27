from app.core.dependencies.common import get_embedding_model, get_qdrant_client, get_yolo_model
from app.infrastructure.vectordb.qdrant import Qdrant
from app.services.fruit.point import FruitPointService
from app.worker.celery_app import celery


@celery.task
def embed_fruit_images():
    fruit_embedding_service = FruitPointService(
        qdrant=Qdrant(get_qdrant_client()),
        embedding_model=get_embedding_model(),
        yolo_model=get_yolo_model()
    )
    return fruit_embedding_service.embed_fruit_images()