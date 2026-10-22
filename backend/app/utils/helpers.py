"""Small helpers shared across the backend."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Query


def sha256_bytes(data: bytes) -> str:
    """Return the hex digest of the given payload."""
    return hashlib.sha256(data).hexdigest()


def paginate(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> tuple[int, int]:
    """Return the validated ``(offset, limit)`` tuple for a pagination query."""
    return (page - 1) * page_size, page_size


def truncate(value: str, limit: int = 500) -> str:
    """Shorten a message so that it can be stored in a database column."""
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def clean_dict(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values from a mapping."""
    return {key: value for key, value in payload.items() if value is not None}


__all__ = ["clean_dict", "paginate", "sha256_bytes", "truncate"]
