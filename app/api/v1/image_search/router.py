from fastapi import APIRouter


router = APIRouter(prefix="/image", tags=["Image Search"])


@router.get('/')
def index():
    return {"message": "Hello Image Search"}