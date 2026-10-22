"""Report model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class ReportRecord(Base, IdMixin, TimestampMixin):
    """Metadata of a generated PDF report."""

    __tablename__ = "reports"

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ready", index=True, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(512), unique=True, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experiment_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship(back_populates="reports")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ReportRecord {self.report_type}:{self.status}>"


__all__ = ["ReportRecord"]
