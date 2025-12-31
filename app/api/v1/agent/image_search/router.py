from fastapi import APIRouter, File, UploadFile

from app.domain.services.agent_service import AgentService


router = APIRouter(prefix="/image", tags=["Agent"])
agent_service = AgentService()


@router.post('/')
async def index(
    file: UploadFile = File(...)
):
    return await agent_service.handle_image(file)