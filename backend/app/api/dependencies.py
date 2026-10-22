"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.session import get_db
from ..models import User
from ..services.auth_service import AuthService
from ..services.experiment_service import ExperimentService
from ..services.image_service import ImageService
from ..services.ml_client import MLServiceClient
from ..services.processing_service import ProcessingService
from ..services.report_service import ReportService
from ..storage import build_storage
from ..utils.errors import UnauthorizedError

DbSession = Annotated[Session, Depends(get_db)]


def get_storage():
    """Return the configured storage backend."""
    return build_storage()


def get_ml_client() -> MLServiceClient:
    """Return a client for the ML service."""
    return MLServiceClient()


def get_current_user(
    session: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """Resolve the user of the current request.

    When authentication is enabled a bearer token or the browser's HttpOnly
    session cookie is required; otherwise the shared demo account is used.
    """
    service = AuthService(session)
    if not settings.auth_enabled:
        return service.current_user()

    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif access_token:
        token = access_token

    if not token:
        raise UnauthorizedError(
            "A bearer token is required for this endpoint.", code="authentication_required"
        )
    return service.resolve_token(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_image_service(session: DbSession, storage=Depends(get_storage)) -> ImageService:
    return ImageService(session, storage=storage, ml_client=MLServiceClient())


def get_processing_service(session: DbSession, storage=Depends(get_storage)) -> ProcessingService:
    return ProcessingService(session, storage=storage)


def get_experiment_service(session: DbSession) -> ExperimentService:
    return ExperimentService(session)


def get_report_service(session: DbSession, storage=Depends(get_storage)) -> ReportService:
    return ReportService(session, storage=storage)


__all__ = [
    "CurrentUser",
    "DbSession",
    "get_current_user",
    "get_experiment_service",
    "get_image_service",
    "get_ml_client",
    "get_processing_service",
    "get_report_service",
    "get_storage",
]
