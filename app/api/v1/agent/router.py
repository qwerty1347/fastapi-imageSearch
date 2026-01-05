from fastapi import APIRouter

from app.api.v1.agent.image_search.router import router as image_search_router


router = APIRouter(prefix="/agent")
router.include_router(image_search_router)


@router.get('/')
async def index():
    return {"message": "Hello Agent"}