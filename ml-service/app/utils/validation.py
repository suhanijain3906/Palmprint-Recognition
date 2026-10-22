"""Request level validation helpers.

Validation never trusts the file extension or the client supplied MIME type.
The container is identified from the magic bytes and cross-checked against
the (untrusted) metadata so that mismatches can be reported explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import InvalidImageError, UnsupportedMediaTypeError
from .image_io import (
    DecodedImage,
    decode_image,
    extension_media_type,
    sniff_media_type,
)

SUPPORTED_MEDIA_TYPES = (
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
)


@dataclass
class ValidationReport:
    """Result of validating a single uploaded payload."""

    filename: str | None
    declared_content_type: str | None
    detected_media_type: str
    detected_format: str
    width: int
    height: int
    channels: int
    size_bytes: int
    extension_matches: bool
    warnings: list[str] = field(default_factory=list)

    @property
    def pixel_count(self) -> int:
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "declared_content_type": self.declared_content_type,
            "detected_media_type": self.detected_media_type,
            "detected_format": self.detected_format,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "size_bytes": self.size_bytes,
            "pixel_count": self.pixel_count,
            "extension_matches": self.extension_matches,
            "warnings": list(self.warnings),
        }


def validate_payload(
    data: bytes,
    *,
    filename: str | None = None,
    declared_content_type: str | None = None,
    max_bytes: int,
    max_pixels: int,
    max_dimension: int,
) -> tuple[DecodedImage, ValidationReport]:
    """Validate and decode an uploaded payload.

    The returned :class:`ValidationReport` describes what was *actually*
    detected, independently of what the client claimed.
    """
    if not data:
        raise InvalidImageError("The uploaded file is empty.")

    detected = sniff_media_type(data)
    if detected is None:
        raise UnsupportedMediaTypeError(
            "Unsupported file type. Supported formats: " + ", ".join(SUPPORTED_MEDIA_TYPES),
            details={"supported_media_types": list(SUPPORTED_MEDIA_TYPES)},
        )

    if detected not in SUPPORTED_MEDIA_TYPES:
        raise UnsupportedMediaTypeError(
            f"Media type '{detected}' is not supported.",
            details={"supported_media_types": list(SUPPORTED_MEDIA_TYPES)},
        )

    decoded = decode_image(
        data,
        max_bytes=max_bytes,
        max_pixels=max_pixels,
        max_dimension=max_dimension,
    )

    warnings: list[str] = []
    extension_type = extension_media_type(filename)
    extension_matches = extension_type is None or extension_type == detected
    if not extension_matches:
        warnings.append(
            f"The file extension implies '{extension_type}' but the content is '{detected}'."
        )

    if declared_content_type and declared_content_type != detected:
        warnings.append(
            f"The client declared '{declared_content_type}' but the content is '{detected}'."
        )

    if decoded.original_format not in {"PNG", "JPEG", "BMP", "TIFF", "WEBP"}:
        warnings.append(
            f"The container reported the format '{decoded.original_format}'; "
            "only PNG, JPEG, BMP, TIFF and WebP are supported."
        )

    report = ValidationReport(
        filename=filename,
        declared_content_type=declared_content_type,
        detected_media_type=decoded.media_type,
        detected_format=decoded.original_format,
        width=decoded.width,
        height=decoded.height,
        channels=decoded.channels,
        size_bytes=len(data),
        extension_matches=extension_matches,
        warnings=warnings,
    )
    return decoded, report
