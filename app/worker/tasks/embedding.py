from app.services.fruit.point import FruitPointService
from app.worker.celery_app import celery


@celery.task
def embed_fruit_images():
    fruit_embedding_service = FruitPointService()
    return fruit_embedding_service.embed_fruit_images()