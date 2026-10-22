"""Repository for user accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User

DEMO_EMAIL = "demo@palmprint.local"


class UserRepository:
    """Data access for :class:`~app.models.user.User`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self._session.execute(statement).scalar_one_or_none()

    def create(self, *, email: str, display_name: str, password_hash: str | None) -> User:
        user = User(
            email=email.lower(),
            display_name=display_name,
            password_hash=password_hash,
        )
        self._session.add(user)
        self._session.flush()
        return user

    def get_or_create_demo_user(self) -> User:
        """Return the shared demo account, creating it on first use.

        The demo account is used when authentication is disabled.  All data
        is then shared, which is why the platform labels this mode clearly.
        """
        user = self.get_by_email(DEMO_EMAIL)
        if user is None:
            user = self.create(
                email=DEMO_EMAIL,
                display_name="Demo researcher",
                password_hash=None,
            )
            user.is_demo_account = True
            self._session.flush()
        return user


__all__ = ["DEMO_EMAIL", "UserRepository"]
