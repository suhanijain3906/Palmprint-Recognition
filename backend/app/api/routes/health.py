"""Health endpoint of the backend."""

from __future__ import annotations

from fastapi import APIRouter

from ...core.config import settings
from ...db.session import engine
from ...schemas.common import HealthResponse
from ...services.ml_client import MLServiceClient
from ...storage import build_storage
from ...utils.errors import ServiceUnavailableError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health")
def health() -> HealthResponse:
    """Report the health of the backend and of its dependencies."""
    database_status = "ok"
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on the environment
        database_status = f"error: {type(exc).__name__}"

    storage_status = "ok"
    try:
        build_storage()
    except Exception as exc:  # pragma: no cover - depends on the environment
        storage_status = f"error: {type(exc).__name__}"

    ml_status: dict[str, object] = {"status": "unknown"}
    try:
        with MLServiceClient() as client:
            payload = client.health()
        ml_status = {
            "status": "ok",
            "service": payload.get("service"),
            "version": payload.get("version"),
            "trained_model_available": bool(
                (payload.get("trained_models") or {}).get("trained_model_available", False)
            ),
        }
    except Exception as exc:
        ml_status = {"status": "unavailable", "reason": type(exc).__name__}

    return HealthResponse(
        status="ok" if database_status == "ok" else "degraded",
        service=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        database=database_status,
        storage=storage_status,
        ml_service=ml_status,
        auth_enabled=settings.auth_enabled,
        demo_mode=not settings.auth_enabled and settings.demo_mode,
    )


@router.get("/ready", summary="Readiness probe")
def ready() -> dict[str, str]:
    """Simple readiness probe used by container health checks."""
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServiceUnavailableError(
            "The database is not reachable.", details={"reason": str(exc)}
        ) from exc
    return {"status": "ready"}


__all__ = ["router"]
