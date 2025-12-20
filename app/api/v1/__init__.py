from fastapi import APIRouter

from common.utils.router import auto_include_domain_routers


api_v1_router = APIRouter(prefix="/api/v1")

auto_include_domain_routers(
    parent_router=api_v1_router,
    base_package="app.api.v1",
)