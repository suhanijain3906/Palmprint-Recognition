"""Shared exception types with a consistent HTTP representation."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for every error that is turned into an HTTP response."""

    status_code: int = 400
    code: str = "bad_request"

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
        if code:
            self.code = code
        if status_code:
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


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedMediaTypeError(AppError):
    status_code = 415
    code = "unsupported_media_type"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"


class UpstreamTimeoutError(AppError):
    status_code = 504
    code = "upstream_timeout"


__all__ = [
    "AppError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "PayloadTooLargeError",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "UnsupportedMediaTypeError",
    "UpstreamTimeoutError",
    "ValidationError",
]
