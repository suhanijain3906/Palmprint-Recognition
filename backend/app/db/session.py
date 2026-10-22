"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings

_CONNECT_ARGS: dict[str, object] = {}
if settings.is_sqlite:
    _CONNECT_ARGS["check_same_thread"] = False


def _ensure_sqlite_directory() -> None:
    """Create the directory of the SQLite file if it does not exist yet."""
    if not settings.is_sqlite:
        return
    raw = settings.database_url.split("sqlite:///", 1)[-1]
    if raw in ("", ":memory:"):
        return
    Path(raw).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory()

engine: Engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
    future=True,
    connect_args=_CONNECT_ARGS,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _configure_sqlite(
    dbapi_connection, connection_record
) -> None:  # pragma: no cover - driver hook
    """Enable foreign key enforcement for SQLite (disabled by default)."""
    if not settings.is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for use outside of the request cycle."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create the tables directly (used for tests and first-run bootstrap)."""
    from ..models import Base

    Base.metadata.create_all(bind=engine)


__all__ = ["SessionLocal", "engine", "get_db", "init_db", "session_scope"]
