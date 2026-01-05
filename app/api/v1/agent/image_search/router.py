from fastapi import APIRouter, File, UploadFile

from app.services.image_search_service import ImageSearchService


router = APIRouter(prefix="/image", tags=["ImageSearch"])
image_search_service = ImageSearchService()


@router.post('/')
async def index(
    file: UploadFile = File(...)
):
    return await image_search_service.handle_image(file)