"""Image upload, validation and storage service."""

from __future__ import annotations

import logging
from typing import Any, BinaryIO

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import ImageRecord, User
from ..repositories import ImageRepository
from ..storage import StorageBackend, StorageError, build_storage, random_key
from ..utils.errors import (
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
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

        The image is validated by the ML service so that the backend never
        has to decode image data itself.  The original file is stored
        unmodified; every derived image is stored separately.
        """
        if not payload:
            raise ValidationError("The uploaded file is empty.", code="empty_upload")

        if len(payload) > settings.max_upload_bytes:
            raise PayloadTooLargeError(
                f"The upload exceeds the configured limit of {settings.max_upload_bytes} bytes.",
                details={"size_bytes": len(payload), "max_bytes": settings.max_upload_bytes},
            )

        if self._ml_client is None:
            raise ValidationError(
                "The image could not be validated because the ML service is not configured.",
                code="validation_unavailable",
            )

        try:
            validation = self._ml_client.validate(
                payload, filename=filename, content_type=content_type or "application/octet-stream"
            )
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Validation call failed")
            raise ValidationError(
                "The image could not be validated.", code="validation_failed"
            ) from exc

        report = validation.get("validation", {})
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
        warnings = list(report.get("warnings", []))
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
