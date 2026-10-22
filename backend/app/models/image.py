"""Image metadata model.

The binary image data is **not** stored in the database.  Only the metadata
and a storage key pointing at the file in the configured storage backend are
persisted.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from .job import ProcessingJob
    from .user import User


class ImageRecord(Base, IdMixin, TimestampMixin):
    """Metadata of an uploaded palmprint image."""

    __tablename__ = "images"

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship(back_populates="images")
    jobs: Mapped[list[ProcessingJob]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ImageRecord {self.id} {self.media_type}>"


__all__ = ["ImageRecord"]
