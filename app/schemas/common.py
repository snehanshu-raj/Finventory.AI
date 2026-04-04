"""Common API response schemas."""

from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard success response envelope."""
    success: bool = True
    data: Any = None
    message: str = "Success"


class ApiErrorDetail(BaseModel):
    """Error detail inside an error response."""
    code: str
    message: str


class ApiErrorResponse(BaseModel):
    """Standard error response envelope."""
    success: bool = False
    error: ApiErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0
