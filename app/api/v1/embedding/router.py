from fastapi import APIRouter

from app.domain.services.vectordb_service import VectorDBService
from common.utils.response import success_response


router = APIRouter(prefix="/embedding", tags=["VectorDB"])
vectordb_service = VectorDBService()


@router.get('/images')
async def index():
    await vectordb_service.handle_fruits_images()
    return success_response()