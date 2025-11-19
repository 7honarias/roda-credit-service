from pydantic import BaseModel
from typing import Optional


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int