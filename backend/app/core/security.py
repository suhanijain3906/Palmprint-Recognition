"""Password hashing and JSON web token helpers.

* Passwords are hashed with **bcrypt**; plaintext passwords are never stored
  and never logged.
* Access tokens are stateless JWTs (``HS256``) with an explicit expiry.
* The secret key lives in the environment.  In production the application
  refuses to start with the default development secret.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from .config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    if not password or len(password) < 8:
        raise ValueError("The password must contain at least 8 characters.")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, *, expires_delta: timedelta | None = None) -> str:
    """Create a signed access token for the given user identifier."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a token; raises ``jwt.PyJWTError`` when invalid."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def constant_time_equals(left: str, right: str) -> bool:
    """Timing safe comparison used for internal service credentials."""
    return hmac.compare_digest(
        hashlib.sha256(left.encode("utf-8")).hexdigest(),
        hashlib.sha256(right.encode("utf-8")).hexdigest(),
    )


__all__ = [
    "ALGORITHM",
    "constant_time_equals",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
