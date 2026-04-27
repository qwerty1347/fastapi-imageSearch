from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    code: str
    data: T


class ErrorResponse(BaseModel, Generic[T]):
    code: str
    message: str | None
    errors: T