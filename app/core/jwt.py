"""JWT token utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.settings import get_settings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    """Create a short-lived access token."""
    settings = get_settings()

    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token."""
    settings = get_settings()

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    settings = get_settings()

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM],
    )
