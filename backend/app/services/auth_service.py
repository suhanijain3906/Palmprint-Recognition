"""Authentication service (optional).

The platform supports two modes:

``AUTH_ENABLED=true``
    Accounts are required.  Passwords are hashed with bcrypt and access
    tokens are short lived JWTs.  Every record is owned by exactly one
    account and ownership is enforced on every read and write.

``AUTH_ENABLED=false`` (academic demo mode)
    Every request is attributed to the shared ``demo`` account.  The mode is
    reported by the API and the UI so that it is never mistaken for a
    production deployment.  In this mode all data is shared between users
    and the deployment must not be exposed to the public internet.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import create_access_token, hash_password, verify_password
from ..models import User
from ..repositories import UserRepository
from ..utils.errors import ConflictError, UnauthorizedError, ValidationError

logger = logging.getLogger("backend.auth_service")


class AuthService:
    """Registration, login and token issuing."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)

    def register(self, *, email: str, display_name: str, password: str) -> tuple[User, str]:
        if self._users.get_by_email(email):
            raise ConflictError(
                "An account with this email address already exists.", code="email_taken"
            )
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            raise ValidationError(str(exc), code="weak_password") from exc

        user = self._users.create(
            email=email, display_name=display_name, password_hash=password_hash
        )
        token = create_access_token(user.id)
        return user, token

    def login(self, *, email: str, password: str) -> tuple[User, str]:
        user = self._users.get_by_email(email)
        if user is None or not user.password_hash:
            raise UnauthorizedError(
                "Invalid email address or password.", code="invalid_credentials"
            )
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError(
                "Invalid email address or password.", code="invalid_credentials"
            )
        if not user.is_active:
            raise UnauthorizedError("This account is disabled.", code="account_disabled")
        token = create_access_token(user.id)
        return user, token

    def resolve_token(self, token: str) -> User:
        from ..core.security import decode_access_token

        try:
            payload = decode_access_token(token)
        except Exception as exc:
            raise UnauthorizedError(
                "The access token is invalid or has expired.", code="invalid_token"
            ) from exc

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("The access token is invalid.", code="invalid_token")
        user = self._users.get(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("The account does not exist any more.", code="invalid_token")
        return user

    def current_user(self) -> User:
        """Return the user of the current request.

        In demo mode the shared demo account is returned; in authenticated
        mode the caller must provide a valid bearer token.
        """
        if not settings.auth_enabled:
            return self._users.get_or_create_demo_user()
        raise UnauthorizedError(
            "This endpoint requires an authenticated account.", code="authentication_required"
        )

    def count_users(self) -> int:
        statement = select(func.count()).select_from(User)
        return int(self._session.execute(statement).scalar_one())


__all__ = ["AuthService"]
