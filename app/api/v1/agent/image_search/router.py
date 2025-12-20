from fastapi import APIRouter


router = APIRouter(prefix="/image-search", tags=["Agent"])


@router.get('/')
async def index():
    return {"message": "Hello ImageSearch"}