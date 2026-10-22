"""Schemas for the processing endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArtifactResponse(BaseModel):
    """A generated output image hosted by the backend."""

    id: str
    kind: str
    media_type: str = "image/png"
    size_bytes: int = 0
    download_url: str


class ProcessingResponse(BaseModel):
    """Uniform response of every processing endpoint."""

    status: str = "success"
    job_id: str
    operation: str
    algorithm: str
    algorithm_version: str | None = None
    image_id: str
    processing_time_ms: float
    metrics: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class JobResponse(BaseModel):
    """A recorded processing job."""

    id: str
    image_id: str | None
    operation: str
    algorithm: str
    algorithm_version: str | None
    status: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


__all__ = ["ArtifactResponse", "JobResponse", "ProcessingResponse"]
