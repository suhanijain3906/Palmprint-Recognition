"""Pydantic schemas of the backend API."""

from .auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    MessageResponse,
    Page,
    PageMeta,
)
from .experiment import (
    DatasetAvailability,
    DatasetResponse,
    ExperimentRequest,
    ExperimentResponse,
    ExperimentResultResponse,
    ReportCreateRequest,
    ReportResponse,
)
from .image import ImageResponse, ImageUpdateRequest, ImageUploadResponse
from .processing import ArtifactResponse, JobResponse, ProcessingResponse
from .recognition import (
    ComparisonRequest,
    ComparisonResponse,
    EvaluationRequest,
    EvaluationResponse,
    RecognitionRequest,
    RecognitionResponse,
)

__all__ = [
    "ArtifactResponse",
    "ComparisonRequest",
    "ComparisonResponse",
    "DatasetAvailability",
    "DatasetResponse",
    "ErrorDetail",
    "ErrorResponse",
    "EvaluationRequest",
    "EvaluationResponse",
    "ExperimentRequest",
    "ExperimentResponse",
    "ExperimentResultResponse",
    "HealthResponse",
    "ImageResponse",
    "ImageUpdateRequest",
    "ImageUploadResponse",
    "JobResponse",
    "LoginRequest",
    "MessageResponse",
    "Page",
    "PageMeta",
    "ProcessingResponse",
    "RecognitionRequest",
    "RecognitionResponse",
    "RegisterRequest",
    "ReportCreateRequest",
    "ReportResponse",
    "TokenResponse",
    "UserResponse",
]
