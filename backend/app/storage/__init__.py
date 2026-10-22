"""Configurable storage layer.

The backend never stores image binaries in the database and never assumes that
the local filesystem is persistent.  Two adapters are provided:

``LocalStorage``
    Writes into a configured directory.  Suitable for local development and
    for deployments with a persistent volume (Docker named volume, PVC, ...).

``S3Storage``
    Writes into an S3 compatible object store.  This is the recommended
    adapter for cloud deployments where the container filesystem is
    ephemeral.  It requires the optional ``boto3`` dependency.
"""

from __future__ import annotations

import io
import os
import secrets
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from ..core.config import settings


def random_key(prefix: str, extension: str = "") -> str:
    """Build a randomised, non guessable storage key.

    The original file name is never used for the stored path, so an attacker
    cannot influence the location of a file on disk.
    """
    extension = extension if extension.startswith(".") or not extension else f".{extension}"
    return f"{prefix}/{secrets.token_urlsafe(24)}{extension}"


class StorageError(RuntimeError):
    """Raised when the storage backend cannot fulfil a request."""


class StorageBackend(ABC):
    """Interface of every storage adapter."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Persist ``data`` under ``key`` and return the key."""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Open the object stored under ``key`` for reading."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Return the content stored under ``key``."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete the object; returns ``True`` when something was removed."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Whether an object exists under ``key``."""

    def size(self, key: str) -> int:
        """Size of the stored object in bytes."""
        with self.open(key) as handle:
            handle.seek(0, io.SEEK_END)
            return handle.tell()

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human readable name of the adapter."""


class LocalStorage(StorageBackend):
    """Filesystem adapter for development and persistent-volume deployments."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def backend_name(self) -> str:
        return "local"

    def _resolve(self, key: str) -> Path:
        """Resolve a key inside the storage root and reject traversal."""
        candidate = (self._root / key).resolve()
        root = self._root.resolve()
        if root != candidate and root not in candidate.parents:
            raise StorageError("Refusing to access a path outside of the storage root.")
        return candidate

    def save(self, key: str, data: bytes) -> str:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, target)
        return key

    def open(self, key: str) -> BinaryIO:
        target = self._resolve(key)
        if not target.is_file():
            raise FileNotFoundError(key)
        return open(target, "rb")

    def read(self, key: str) -> bytes:
        with self.open(key) as handle:
            return handle.read()

    def delete(self, key: str) -> bool:
        target = self._resolve(key)
        if target.is_file():
            target.unlink()
            return True
        return False

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except StorageError:
            return False


class S3Storage(StorageBackend):
    """S3 compatible object storage adapter."""

    def __init__(
        self,
        bucket: str,
        *,
        endpoint_url: str | None = None,
        region: str = "us-east-1",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        use_path_style: bool = True,
    ) -> None:
        try:
            import boto3  # noqa: PLC0415
            from botocore.config import Config  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise StorageError(
                "The 's3' storage backend requires the optional 'boto3' dependency."
            ) from exc

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                s3={"addressing_style": "path" if use_path_style else "auto"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    @property
    def backend_name(self) -> str:
        return "s3"

    def save(self, key: str, data: bytes) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType="application/octet-stream",
        )
        return key

    def open(self, key: str) -> BinaryIO:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except Exception as exc:  # pragma: no cover - network dependent
            raise FileNotFoundError(key) from exc
        return io.BytesIO(response["Body"].read())

    def read(self, key: str) -> bytes:
        with self.open(key) as handle:
            return handle.read()

    def delete(self, key: str) -> bool:
        self._client.delete_object(Bucket=self._bucket, Key=key)
        return True

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError  # pragma: no cover

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError:
            return False
        return True


def build_storage() -> StorageBackend:
    """Instantiate the storage adapter selected in the configuration."""
    if settings.storage_backend == "s3":
        if not settings.s3_bucket:
            raise StorageError("S3_BUCKET must be configured when STORAGE_BACKEND=s3 is selected.")
        return S3Storage(
            settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            use_path_style=settings.s3_use_path_style,
        )
    return LocalStorage(settings.storage_root)


__all__ = [
    "LocalStorage",
    "S3Storage",
    "StorageBackend",
    "StorageError",
    "build_storage",
    "random_key",
]
