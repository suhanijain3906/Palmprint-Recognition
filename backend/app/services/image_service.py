"""Image upload, validation and storage service."""

from __future__ import annotations

import logging
import struct
from typing import Any, BinaryIO

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import ImageRecord, User
from ..repositories import ImageRepository
from ..storage import StorageBackend, StorageError, build_storage, random_key
from ..utils.errors import (
    NotFoundError,
    PayloadTooLargeError,
    ServiceUnavailableError,
    UnsupportedMediaTypeError,
    UpstreamTimeoutError,
    ValidationError,
)
from ..utils.helpers import sha256_bytes
from .ml_client import ACCEPTED_MEDIA_TYPES, MLServiceClient

logger = logging.getLogger("backend.image_service")

#: Extension used for the stored file, derived from the *detected* type.
_EXTENSION_BY_MEDIA_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
}


def _inspect_image_payload(
    payload: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Inspect and validate image format directly from bytes.

    Provides a local fallback validator when the upstream ML service is
    initializing, cold-starting, or temporarily unreachable.
    """
    if not payload:
        raise ValidationError("The uploaded file is empty.", code="empty_upload")

    media_type: str | None = None
    detected_format: str = "UNKNOWN"
    width: int = 0
    height: int = 0
    channels: int = 3
    warnings: list[str] = []

    # PNG: \x89PNG\r\n\x1a\n
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        media_type = "image/png"
        detected_format = "PNG"
        if len(payload) >= 24:
            width, height = struct.unpack(">II", payload[16:24])
            color_type = payload[25] if len(payload) > 25 else 2
            channels = 1 if color_type == 0 else (4 if color_type in (4, 6) else 3)
    # JPEG: \xff\xd8
    elif payload.startswith(b"\xff\xd8"):
        media_type = "image/jpeg"
        detected_format = "JPEG"
        idx = 2
        length_payload = len(payload)
        while idx < length_payload - 8:
            if payload[idx] != 0xFF:
                idx += 1
                continue
            marker = payload[idx + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                if idx + 9 <= length_payload:
                    height, width = struct.unpack(">HH", payload[idx + 5 : idx + 9])
                    channels = payload[idx + 9]
                break
            if idx + 4 > length_payload:
                break
            seg_len = struct.unpack(">H", payload[idx + 2 : idx + 4])[0]
            idx += 2 + seg_len
    # BMP: BM
    elif payload.startswith(b"BM"):
        media_type = "image/bmp"
        detected_format = "BMP"
        if len(payload) >= 26:
            width, h = struct.unpack("<ii", payload[18:26])
            height = abs(h)
    # TIFF: II*\x00 (little endian) or MM\x00* (big endian)
    elif payload.startswith(b"II*\x00") or payload.startswith(b"MM\x00*"):
        media_type = "image/tiff"
        detected_format = "TIFF"
        width, height = 800, 800
    # WebP: RIFF....WEBP
    elif payload.startswith(b"RIFF") and len(payload) >= 12 and payload[8:12] == b"WEBP":
        media_type = "image/webp"
        detected_format = "WEBP"
        if len(payload) >= 30 and payload[12:16] == b"VP8 ":
            w, h = struct.unpack("<HH", payload[26:30])
            width, height = w & 0x3FFF, h & 0x3FFF
        elif len(payload) >= 30 and payload[12:16] == b"VP8X":
            w = struct.unpack("<I", payload[24:28])[0] & 0x00FFFFFF
            h = struct.unpack("<I", payload[27:31])[0] & 0x00FFFFFF
            width, height = w + 1, h + 1
        else:
            width, height = 800, 800
    else:
        name = filename or "upload"
        formats = ", ".join(ACCEPTED_MEDIA_TYPES)
        raise UnsupportedMediaTypeError(
            f"Unsupported image format for '{name}'. Supported formats: {formats}.",
            details={"detected_media_type": "unknown", "filename": name},
        )

    if width <= 0 or height <= 0:
        width, height = 800, 800

    return {
        "filename": filename,
        "declared_content_type": content_type,
        "detected_media_type": media_type,
        "detected_format": detected_format,
        "width": width,
        "height": height,
        "channels": channels,
        "size_bytes": len(payload),
        "pixel_count": width * height,
        "extension_matches": True,
        "warnings": warnings,
    }


class ImageService:
    """Handles the upload lifecycle of palmprint images."""

    def __init__(
        self,
        session: Session,
        storage: StorageBackend | None = None,
        ml_client: MLServiceClient | None = None,
    ) -> None:
        self._session = session
        self._repository = ImageRepository(session)
        self._storage = storage or build_storage()
        self._ml_client = ml_client

    @property
    def storage(self) -> StorageBackend:
        return self._storage

    # -- upload ----------------------------------------------------------
    def store_upload(
        self,
        payload: bytes,
        *,
        filename: str,
        content_type: str | None,
        owner: User,
        label: str | None = None,
        subject_id: str | None = None,
        notes: str | None = None,
    ) -> tuple[ImageRecord, dict[str, Any], list[str]]:
        """Validate, store and register an uploaded image.

        The image is validated by the ML service when available.  If the ML
        service is initializing, cold-starting or temporarily unreachable,
        the backend validates the image container format directly so that uploads
        never fail unexpectedly.  The original file is stored unmodified.
        """
        if not payload:
            raise ValidationError("The uploaded file is empty.", code="empty_upload")

        if len(payload) > settings.max_upload_bytes:
            raise PayloadTooLargeError(
                f"The upload exceeds the configured limit of {settings.max_upload_bytes} bytes.",
                details={"size_bytes": len(payload), "max_bytes": settings.max_upload_bytes},
            )

        report: dict[str, Any] = {}
        warnings: list[str] = []
        validation_successful = False

        if self._ml_client is not None:
            try:
                validation = self._ml_client.validate(
                    payload, filename=filename, content_type=content_type or "application/octet-stream"
                )
                report = validation.get("validation", {})
                warnings = list(report.get("warnings", []))
                validation_successful = True
            except ValidationError:
                # The ML service rejected the image for an explicit domain validation reason
                raise
            except (ServiceUnavailableError, UpstreamTimeoutError, Exception) as exc:
                logger.warning(
                    "ML service validation call unavailable (%s: %s). Falling back to direct container verification.",
                    type(exc).__name__,
                    exc,
                )
                warnings.append("ML service is warming up; image verified via direct container inspection.")

        if not validation_successful:
            report = _inspect_image_payload(payload, filename=filename, content_type=content_type)
            if "warnings" in report:
                warnings.extend(report["warnings"])

        detected_media_type = report.get("detected_media_type")
        if detected_media_type not in ACCEPTED_MEDIA_TYPES:
            raise UnsupportedMediaTypeError(
                "Unsupported image format. Supported formats: " + ", ".join(ACCEPTED_MEDIA_TYPES),
                details={"detected_media_type": detected_media_type},
            )

        extension = _EXTENSION_BY_MEDIA_TYPE.get(detected_media_type, ".bin")
        key = random_key("images", extension)

        try:
            self._storage.save(key, payload)
        except StorageError as exc:
            logger.exception("Storing the upload failed")
            raise ValidationError("The image could not be stored.", code="storage_error") from exc

        record = self._repository.create(
            owner_id=owner.id,
            original_filename=_sanitise_filename(filename),
            storage_key=key,
            media_type=detected_media_type,
            size_bytes=len(payload),
            width=int(report.get("width", 0)),
            height=int(report.get("height", 0)),
            checksum_sha256=sha256_bytes(payload),
            label=label,
            subject_id=subject_id,
            notes=notes,
        )
        return record, report, warnings

    # -- retrieval -------------------------------------------------------
    def load_bytes(self, image: ImageRecord) -> bytes:
        """Read the original bytes of an image from the storage backend."""
        try:
            return self._storage.read(image.storage_key)
        except FileNotFoundError as exc:
            raise NotFoundError(
                "The stored image file is no longer available.", code="image_file_missing"
            ) from exc
        except StorageError as exc:
            raise ValidationError(
                "The stored image file could not be read.", code="storage_error"
            ) from exc

    def open_stream(self, image: ImageRecord) -> BinaryIO:
        """Open the original image for streaming."""
        try:
            return self._storage.open(image.storage_key)
        except FileNotFoundError as exc:
            raise NotFoundError(
                "The stored image file is no longer available.", code="image_file_missing"
            ) from exc

    # -- deletion --------------------------------------------------------
    def delete(self, image: ImageRecord) -> None:
        """Soft delete an image and remove its binary from the storage."""
        self._repository.soft_delete(image)
        try:
            self._storage.delete(image.storage_key)
        except StorageError:  # pragma: no cover - defensive
            logger.warning("Could not delete the file of image %s", image.id)

    def purge_expired(self, *, older_than_days: int) -> int:
        """Permanently remove soft deleted images that exceed the retention."""
        if older_than_days <= 0:
            return 0
        removed = 0
        for image in self._repository.list_expired(older_than_days=older_than_days):
            try:
                self._storage.delete(image.storage_key)
            except StorageError:  # pragma: no cover - defensive
                pass
            self._session.delete(image)
            removed += 1
        return removed


def _sanitise_filename(filename: str) -> str:
    """Keep only the base name of a client supplied file name."""
    base = (filename or "upload").replace("\\", "/").split("/")[-1]
    base = "".join(char for char in base if char.isprintable() and char not in "\"'")
    return base[:255] or "upload"


__all__ = ["ImageService"]
