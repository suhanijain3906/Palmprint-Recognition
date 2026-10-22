"""Schemas for experiments, datasets and reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExperimentRequest(BaseModel):
    """Configuration of a research experiment."""

    name: str = Field(..., min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    operation: str = Field(default="enhancement", max_length=64)
    algorithm: str = Field(default="clahe", max_length=64)
    parameters: dict[str, Any] = Field(default_factory=dict)
    image_ids: list[str] = Field(default_factory=list, max_length=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "CLAHE parameter sweep",
                "description": "Compare CLAHE clip limits on three captures.",
                "operation": "enhancement",
                "algorithm": "clahe",
                "parameters": {"clip_limit": 3.0, "tile_grid_size": 8},
                "image_ids": ["1f0c1e0a9b7d4f5e8a1b2c3d4e5f6071"],
            }
        }
    }


class ExperimentResultResponse(BaseModel):
    id: str
    kind: str
    label: str | None = None
    value: float | None = None
    unit: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    image_id: str | None = None
    order_index: int = 0


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    operation: str
    algorithm: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    image_ids: list[str] = Field(default_factory=list)
    status: str
    duration_ms: float | None = None
    error_message: str | None = None
    report_id: str | None = None
    created_at: datetime
    results: list[ExperimentResultResponse] = Field(default_factory=list)


class DatasetAvailability(BaseModel):
    """Whether a dataset is installed in this deployment."""

    status: str = Field(..., description="installed | not_installed | restricted")
    installed: bool = False
    verified_image_count: int | None = None
    verified_subject_count: int | None = None
    local_path: str | None = None
    message: str = ""


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    official_source: str
    licence: str
    access_requirements: str
    modality: str
    reference: str | None = None
    availability: DatasetAvailability
    notes: str | None = None


class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    status: str
    size_bytes: int | None = None
    experiment_id: str | None = None
    job_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    generated_at: datetime | None = None
    download_url: str | None = None


class ReportCreateRequest(BaseModel):
    """Request body for a report that is generated on demand."""

    title: str = Field(default="Palmprint processing report", max_length=200)
    report_type: str = Field(default="processing", max_length=48)
    job_ids: list[str] = Field(default_factory=list, max_length=50)
    experiment_id: str | None = None
    include_images: bool = False


__all__ = [
    "DatasetAvailability",
    "DatasetResponse",
    "ExperimentRequest",
    "ExperimentResponse",
    "ExperimentResultResponse",
    "ReportCreateRequest",
    "ReportResponse",
]
