"""Schemas for image records and uploads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ImageResponse(BaseModel):
    """Metadata of a stored image."""

    id: str
    original_filename: str
    media_type: str
    size_bytes: int
    width: int
    height: int
    checksum_sha256: str
    label: str | None = None
    subject_id: str | None = None
    notes: str | None = None
    created_at: datetime
    download_url: str
    processing_status: str | None = None
    last_operation: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "1f0c1e0a9b7d4f5e8a1b2c3d4e5f6071",
                "original_filename": "capture.png",
                "media_type": "image/png",
                "size_bytes": 51234,
                "width": 640,
                "height": 480,
                "checksum_sha256": "0" * 64,
            }
        }
    }


class ImageUploadResponse(BaseModel):
    """Response of a successful upload."""

    status: str = "success"
    image: ImageResponse
    validation: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ImageUpdateRequest(BaseModel):
    """Optional annotations for an uploaded image."""

    label: str | None = Field(default=None, max_length=120)
    subject_id: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


__all__ = ["ImageResponse", "ImageUpdateRequest", "ImageUploadResponse"]
