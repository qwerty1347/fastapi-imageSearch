from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.dependencies.image_search import get_fruit_search_service
from app.core.utils.response import success_response
from app.schemas.image_search.response import ImageSearchResponse
from app.services.fruit.search import FruitSearchService


router = APIRouter(prefix="/image", tags=["Image Search"])

@router.post('/', response_model=ImageSearchResponse)
async def get_similarity_images(
  file: UploadFile = File(...),
  fruit_search_service: FruitSearchService = Depends(get_fruit_search_service)
) -> JSONResponse:
    result = await fruit_search_service.get_similarity_images(file)
    return success_response(jsonable_encoder(result))