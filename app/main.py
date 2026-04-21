from fastapi import FastAPI

from app.api import api_router
from app.core.exceptions.handler import add_exception_handler
from app.core.logging import setup_logging


app = FastAPI()
setup_logging()
app.include_router(api_router)
add_exception_handler(app)

@app.get('/')
def index():
    return {"message": "Hello FastAPI"}