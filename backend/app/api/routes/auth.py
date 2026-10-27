"""Authentication endpoints (optional)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Response, status

from ...core.config import settings
from ...schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ...services.auth_service import AuthService
from ...utils.errors import ForbiddenError
from ..dependencies import CurrentUser, DbSession

logger = logging.getLogger("backend.routes.auth")

router = APIRouter(prefix="/auth", tags=["authentication"])


def _token_response(user, token: str) -> TokenResponse:
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_demo_account=user.is_demo_account,
        ),
    )


def _set_session_cookie(response: Response, token: str) -> None:
    """Store the JWT in an HttpOnly cookie for the browser frontend.

    SameSite=Lax prevents cross-site state-changing requests from carrying
    the cookie. Secure is enabled in production (HTTPS only).
    """
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


@router.get("/mode", summary="Describe the authentication mode")
def auth_mode() -> dict:
    """Report whether the deployment requires authentication."""
    return {
        "auth_enabled": settings.auth_enabled,
        "allow_registration": settings.allow_registration,
        "mode": "authenticated" if settings.auth_enabled else "academic_demo",
        "message": (
            "Accounts are required for this deployment."
            if settings.auth_enabled
            else "This deployment runs in the academic demo mode: all data is "
            "shared between visitors and no access control is applied. Do not "
            "expose it to the public internet."
        ),
    }


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(payload: RegisterRequest, session: DbSession, response: Response) -> TokenResponse:
    """Register a new account and return an access token."""
    if not settings.allow_registration:
        raise ForbiddenError(
            "Self-service registration is disabled for this deployment.",
            code="registration_disabled",
        )
    service = AuthService(session)
    user, token = service.register(
        email=str(payload.email),
        display_name=payload.display_name,
        password=payload.password,
    )
    _set_session_cookie(response, token)
    return _token_response(user, token)


@router.post("/login", response_model=TokenResponse, summary="Log in")
def login(payload: LoginRequest, session: DbSession, response: Response) -> TokenResponse:
    """Exchange credentials for an access token."""
    service = AuthService(session)
    user, token = service.login(
        email=str(payload.email),
        password=payload.password,
    )
    _set_session_cookie(response, token)
    return _token_response(user, token)


@router.post("/logout", summary="Log out")
def logout(response: Response) -> dict[str, str]:
    """Clear the browser session cookie."""
    response.delete_cookie("access_token", path="/")
    return {"status": "ok", "message": "Logged out."}


@router.get("/me", response_model=UserResponse, summary="Describe the current user")
def me(user: CurrentUser) -> UserResponse:
    """Return the account of the current request."""
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_demo_account=user.is_demo_account,
    )


__all__ = ["router"]
