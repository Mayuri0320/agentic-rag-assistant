"""Tests for authentication schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin, UserRegister


def test_user_register() -> None:
    """Valid registration data should be accepted."""
    user = UserRegister(
        email="user@example.com",
        password="StrongPassword123!",
    )

    assert user.email == "user@example.com"
    assert user.password == "StrongPassword123!"


def test_user_register_rejects_short_password() -> None:
    """Passwords shorter than eight characters should be rejected."""
    with pytest.raises(ValidationError):
        UserRegister(
            email="user@example.com",
            password="short",
        )


def test_user_register_rejects_invalid_email() -> None:
    """Invalid email addresses should be rejected."""
    with pytest.raises(ValidationError):
        UserRegister(
            email="not-an-email",
            password="StrongPassword123!",
        )


def test_user_login() -> None:
    """Valid login data should be accepted."""
    user = UserLogin(
        email="user@example.com",
        password="StrongPassword123!",
    )

    assert user.email == "user@example.com"
