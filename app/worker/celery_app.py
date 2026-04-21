from celery import Celery

from app.core.config import config


celery = Celery(
    "fastapi_imageSearch",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

celery.conf.task_queues = {
    "embedding": {}
}
celery.conf.task_default_queue = "embedding"


import app.worker.tasks  # noqa: F401