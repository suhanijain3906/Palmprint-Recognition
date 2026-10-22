"""Shared API schemas."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail


class MessageResponse(BaseModel):
    status: str = "success"
    message: str


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class Page(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database: str
    storage: str
    ml_service: dict[str, Any] = Field(default_factory=dict)
    auth_enabled: bool
    demo_mode: bool


__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    "Page",
    "PageMeta",
]
