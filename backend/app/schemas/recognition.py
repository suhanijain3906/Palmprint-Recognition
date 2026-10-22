"""Schemas for recognition and comparison endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .processing import ArtifactResponse


class RecognitionRequest(BaseModel):
    """Compare two stored images."""

    image_a_id: str = Field(..., min_length=8, max_length=64)
    image_b_id: str = Field(..., min_length=8, max_length=64)
    detector: str = Field(default="orb", max_length=32)
    lowe_ratio: float = Field(default=0.75, gt=0.0, lt=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "image_a_id": "1f0c1e0a9b7d4f5e8a1b2c3d4e5f6071",
                "image_b_id": "aabbccddeeff00112233445566778899",
                "detector": "orb",
                "lowe_ratio": 0.75,
            }
        }
    }


class RecognitionResponse(BaseModel):
    """Outcome of an experimental comparison."""

    status: str = "success"
    job_id: str
    similarity_score: float | None = None
    score_kind: str
    is_trained_model: bool = False
    is_calibrated_probability: bool = False
    trained_model_available: bool = False
    matcher: str
    matcher_version: str
    details: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class ComparisonRequest(BaseModel):
    """Side-by-side comparison of two stored images."""

    image_a_id: str = Field(..., min_length=8, max_length=64)
    image_b_id: str = Field(..., min_length=8, max_length=64)


class ComparisonResponse(BaseModel):
    """Outcome of a pixel level comparison."""

    status: str = "success"
    job_id: str
    psnr_db: float | None = None
    ssim: float | None = None
    aligned: bool = True
    resized: bool = False
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class EvaluationRequest(BaseModel):
    """Labelled comparison scores for a genuine/impostor evaluation."""

    scores: list[float] = Field(..., min_length=1)
    labels: list[int] = Field(..., min_length=1)
    thresholds: list[float] | None = None


class EvaluationResponse(BaseModel):
    """Metrics computed from labelled comparison scores."""

    status: str = "success"
    auc: float
    roc: dict[str, Any] = Field(default_factory=dict)
    far: dict[str, Any] = Field(default_factory=dict)
    frr: dict[str, Any] = Field(default_factory=dict)
    eer: dict[str, Any] = Field(default_factory=dict)
    counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


__all__ = [
    "ComparisonRequest",
    "ComparisonResponse",
    "EvaluationRequest",
    "EvaluationResponse",
    "RecognitionRequest",
    "RecognitionResponse",
]
