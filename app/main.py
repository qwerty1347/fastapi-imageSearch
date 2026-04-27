from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import config
from app.core.exceptions.handler import add_exception_handler
from app.core.logging import setup_logging


app = FastAPI()
setup_logging()
app.include_router(api_router)
add_exception_handler(app)

origins = config.ALLOWED_ORIGINS.split(",") if config.ALLOWED_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def index():
    return {"message": "Hello FastAPI"}