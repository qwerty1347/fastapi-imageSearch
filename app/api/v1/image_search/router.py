from fastapi import APIRouter, File, UploadFile

from app.services.fruit.search import FruitSearchService


router = APIRouter(prefix="/image", tags=["Image Search"])
fruit_search_service = FruitSearchService()

@router.post('/')
async def get_similarity_images(
    file: UploadFile = File(...)
):
    response = await fruit_search_service.get_similarity_images(file)

    return {"message": "Hello Image Search"}