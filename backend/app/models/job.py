"""Processing job model.

Every call to a processing endpoint creates a job record so that the history
page and the dashboard can show what was actually executed, with which
parameters and how long it took.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from .image import ImageRecord


class ProcessingJob(Base, IdMixin, TimestampMixin):
    """A single processing operation applied to an image."""

    __tablename__ = "processing_jobs"

    owner_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    image_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("images.id", ondelete="CASCADE"), index=True, nullable=True
    )
    operation: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    algorithm_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="succeeded", index=True, nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    image: Mapped[ImageRecord | None] = relationship(back_populates="jobs")

    @property
    def parameters(self) -> dict[str, Any]:
        try:
            return json.loads(self.parameters_json or "{}")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return {}

    @property
    def metrics(self) -> dict[str, Any]:
        try:
            return json.loads(self.metrics_json or "{}")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return {}

    @property
    def warnings(self) -> list[str]:
        try:
            return json.loads(self.warnings_json or "[]")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return []

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ProcessingJob {self.operation}:{self.status}>"


__all__ = ["ProcessingJob"]
