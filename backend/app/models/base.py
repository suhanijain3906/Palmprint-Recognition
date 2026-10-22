"""Declarative base and shared column helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class of every ORM model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    """Timezone aware ``now`` used for every timestamp column."""
    return datetime.now(UTC)


def new_uuid() -> str:
    """Return a random identifier for user facing objects."""
    return uuid.uuid4().hex


class TimestampMixin:
    """Adds creation and update timestamps to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class IdMixin:
    """Adds a random string primary key.

    A random (non sequential) identifier avoids leaking the number of stored
    records and works identically on SQLite and PostgreSQL.
    """

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_uuid)


__all__ = ["Base", "IdMixin", "NAMING_CONVENTION", "TimestampMixin", "new_uuid", "utcnow"]
