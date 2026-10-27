"""Database bootstrap executed when the application starts.

Managed platforms often start a fresh container with an empty database and no
chance to run a separate release command.  The application therefore applies
the Alembic migrations itself on startup.  If Alembic is unavailable or the
database was created without a version table, it falls back to creating the
missing tables directly so that the service still becomes usable.
"""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from ..core.config import settings
from .session import engine, init_db

logger = logging.getLogger("backend.db.bootstrap")

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config | None:
    ini = _BACKEND_ROOT / "alembic.ini"
    migrations = _BACKEND_ROOT / "migrations"
    if not ini.is_file() or not migrations.is_dir():
        return None
    config = Config(str(ini))
    config.set_main_option("script_location", str(migrations))
    config.set_main_option("prepend_sys_path", str(_BACKEND_ROOT))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def _ensure_demo_user() -> None:
    """Pre-create the demo user so the first request never hits a race condition."""
    if settings.auth_enabled:
        return
    try:
        from .session import SessionLocal
        from ..repositories.user_repository import UserRepository

        with SessionLocal() as session:
            repo = UserRepository(session)
            repo.get_or_create_demo_user()
            session.commit()
    except Exception:
        logger.exception("Could not pre-create demo user.")


def ensure_database_schema() -> None:
    """Bring the database schema up to date, creating it if necessary."""
    if settings.environment == "testing" or not settings.auto_migrate:
        return

    config = _alembic_config()
    if config is None:
        logger.warning("Alembic configuration is missing; creating the schema directly.")
        init_db()
        _ensure_demo_user()
        return

    try:
        command.upgrade(config, "head")
        logger.info("Database migrations are up to date.")
        _ensure_demo_user()
        return
    except Exception:  # pragma: no cover - depends on the deployed database
        logger.exception("Alembic upgrade failed; attempting a safe schema bootstrap.")

    from ..models import Base

    expected = {table.name for table in Base.metadata.sorted_tables}
    present = set(inspect(engine).get_table_names())

    if expected.issubset(present) and "alembic_version" not in present:
        try:
            command.stamp(config, "head")
            logger.warning("Existing schema stamped at the Alembic head revision.")
            _ensure_demo_user()
            return
        except Exception:  # pragma: no cover - defensive
            logger.exception("Could not stamp the existing schema.")

    init_db()
    _ensure_demo_user()
    logger.warning(
        "Created missing database tables without Alembic. "
        "Run 'alembic upgrade head' when a migration is available."
    )


__all__ = ["ensure_database_schema"]
