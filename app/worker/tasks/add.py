from app.worker.celery_app import celery


@celery.task
def add(x: int, y: int):
    return x + y