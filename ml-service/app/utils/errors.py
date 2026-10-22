"""Shared error types for the ML service.

The API layer converts these into structured JSON error payloads so that the
backend (and ultimately the frontend) can react to a machine readable error
code instead of parsing prose.
"""

from __future__ import annotations

from typing import Any


class MLServiceError(Exception):
    """Base class for every error raised by the ML service."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


class InvalidImageError(MLServiceError):
    """The uploaded payload is not a decodable, supported raster image."""

    status_code = 415
    code = "invalid_image"


class UnsupportedMediaTypeError(MLServiceError):
    """The uploaded payload is not one of the supported raster formats."""

    status_code = 415
    code = "unsupported_media_type"


class PayloadTooLargeError(MLServiceError):
    """The uploaded payload exceeds the configured size limits."""

    status_code = 413
    code = "payload_too_large"


class AlgorithmError(MLServiceError):
    """An algorithm could not produce a result for the given input."""

    status_code = 422
    code = "algorithm_error"


class InsufficientFeaturesError(AlgorithmError):
    """Not enough detectable features to run the requested operation."""

    status_code = 422
    code = "insufficient_features"


class ArtifactNotFoundError(MLServiceError):
    status_code = 404
    code = "artifact_not_found"


class EvaluationError(MLServiceError):
    """The evaluation request is not methodologically valid."""

    status_code = 422
    code = "invalid_evaluation_request"
