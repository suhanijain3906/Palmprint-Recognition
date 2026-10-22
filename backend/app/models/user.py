"""User account model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from .experiment import Experiment
    from .image import ImageRecord
    from .report import ReportRecord


class User(Base, IdMixin, TimestampMixin):
    """A platform account.

    When authentication is disabled every request is attributed to the
    shared ``demo`` account, which is flagged with ``is_demo_account``.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo_account: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    images: Mapped[list[ImageRecord]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    experiments: Mapped[list[Experiment]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    reports: Mapped[list[ReportRecord]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email}>"


__all__ = ["User"]
