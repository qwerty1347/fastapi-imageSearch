from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router_collector import get_api_routers
from common.exceptions.handlers import register_exception_handlers
from config.settings import settings


app = FastAPI()
origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for router in get_api_routers():
    app.include_router(router)

app.mount(
    "/static",
    StaticFiles(directory=settings.STORAGE_PATH),
    name="static",
)


@app.get('/')
async def root():
    return {"message": "Hello FastAPI"}