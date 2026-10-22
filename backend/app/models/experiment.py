"""Experiment and experiment result models."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class Experiment(Base, IdMixin, TimestampMixin):
    """A configured research experiment."""

    __tablename__ = "experiments"

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    image_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="completed", index=True, nullable=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    report_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    owner: Mapped[User] = relationship(back_populates="experiments")
    results: Mapped[list[ExperimentResult]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )

    @property
    def parameters(self) -> dict[str, Any]:
        try:
            return json.loads(self.parameters_json or "{}")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return {}

    @property
    def image_ids(self) -> list[str]:
        try:
            return json.loads(self.image_ids_json or "[]")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return []


class ExperimentResult(Base, IdMixin, TimestampMixin):
    """A measured result of a single experiment run."""

    __tablename__ = "experiment_results"

    experiment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    experiment: Mapped[Experiment] = relationship(back_populates="results")

    @property
    def details(self) -> dict[str, Any]:
        try:
            return json.loads(self.details_json or "{}")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return {}


__all__ = ["Experiment", "ExperimentResult"]
