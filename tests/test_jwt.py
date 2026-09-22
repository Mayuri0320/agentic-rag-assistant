"""Tests for JWT utilities."""

from datetime import UTC, datetime

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token() -> None:
    """Access token should contain the correct user and token type."""
    token = create_access_token(1)

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert datetime.fromtimestamp(payload["exp"], tz=UTC) > datetime.now(UTC)


def test_refresh_token() -> None:
    """Refresh token should contain the correct user and token type."""
    token = create_refresh_token(1)

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"


def test_invalid_token() -> None:
    """Invalid JWT should be rejected."""
    invalid_token = "invalid.token.value"

    try:
        decode_token(invalid_token)
    except ValueError as exc:
        assert str(exc) == "Invalid or expired token"
    else:
        raise AssertionError("Invalid token was accepted")
