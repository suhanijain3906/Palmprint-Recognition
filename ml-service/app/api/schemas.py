"""Pydantic response models for the ML service API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AlgorithmInfo(BaseModel):
    """Identifier of the algorithm that produced a result."""

    name: str
    version: str | None = None
    anatomical: bool | None = None
    description: str | None = None


class ArtifactRef(BaseModel):
    """Reference to a stored output image."""

    id: str
    kind: str
    media_type: str = "image/png"
    size_bytes: int = 0
    download_path: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail


class BaseResult(BaseModel):
    """Common envelope shared by every successful response."""

    status: str = "success"
    algorithm: AlgorithmInfo | None = None
    processing_time_ms: float = 0.0
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ValidationResult(BaseResult):
    validation: dict[str, Any] = Field(default_factory=dict)


class ROIResultResponse(BaseResult):
    roi: dict[str, Any] = Field(default_factory=dict)


class EnhancementResultResponse(BaseResult):
    enhancement: dict[str, Any] = Field(default_factory=dict)


class QualityResultResponse(BaseResult):
    quality: dict[str, Any] = Field(default_factory=dict)


class FeatureResultResponse(BaseResult):
    features: dict[str, Any] = Field(default_factory=dict)


class RecognitionResultResponse(BaseResult):
    recognition: dict[str, Any] = Field(default_factory=dict)


class LandmarkResultResponse(BaseResult):
    landmarks: dict[str, Any] = Field(default_factory=dict)


class ComparisonResultResponse(BaseResult):
    comparison: dict[str, Any] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    """Labelled comparison scores for a genuine/impostor evaluation."""

    scores: list[float] = Field(..., min_length=1, description="Similarity scores per comparison.")
    labels: list[int] = Field(..., min_length=1, description="1 = genuine, 0 = impostor.")
    thresholds: list[float] | None = Field(
        default=None, description="Optional operating thresholds for the FAR/FRR table."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "scores": [0.82, 0.31, 0.74, 0.12],
                "labels": [1, 0, 1, 0],
            }
        }
    }


class EvaluationResultResponse(BaseResult):
    evaluation: dict[str, Any] = Field(default_factory=dict)


class AlgorithmCatalogueEntry(BaseModel):
    name: str
    type: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
    trained_models: dict[str, Any] = Field(default_factory=dict)
    algorithms: list[str] = Field(default_factory=list)


__all__ = [
    "AlgorithmCatalogueEntry",
    "AlgorithmInfo",
    "ArtifactRef",
    "BaseResult",
    "ComparisonResultResponse",
    "EnhancementResultResponse",
    "ErrorDetail",
    "ErrorResponse",
    "EvaluationRequest",
    "EvaluationResultResponse",
    "FeatureResultResponse",
    "HealthResponse",
    "LandmarkResultResponse",
    "QualityResultResponse",
    "ROIResultResponse",
    "RecognitionResultResponse",
    "ValidationResult",
]
