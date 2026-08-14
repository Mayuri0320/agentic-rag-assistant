"""Tests for authentication service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.auth import UserRegister
from app.services.auth_service import AuthenticationService


@pytest.mark.anyio
async def test_register_user() -> None:
    """Registration should create a user and return tokens."""
    session = MagicMock()

    service = AuthenticationService(session)

    user = MagicMock()
    user.id = 1

    with (
        patch.object(
            service.repository,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch.object(
            service.repository,
            "create",
            new_callable=AsyncMock,
            return_value=user,
        ),
        patch(
            "app.services.auth_service.create_access_token",
            return_value="access-token",
        ),
        patch(
            "app.services.auth_service.create_refresh_token",
            return_value="refresh-token",
        ),
    ):
        result = await service.register(
            UserRegister(
                email="user@example.com",
                password="StrongPassword123!",
            )
        )

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"
    assert result.token_type == "bearer"


@pytest.mark.anyio
async def test_register_existing_user() -> None:
    """Registration should reject an existing email."""
    session = MagicMock()

    service = AuthenticationService(session)

    existing_user = MagicMock()

    with patch.object(
        service.repository,
        "get_by_email",
        new_callable=AsyncMock,
        return_value=existing_user,
    ):
        with pytest.raises(ValueError, match="already exists"):
            await service.register(
                UserRegister(
                    email="user@example.com",
                    password="StrongPassword123!",
                )
            )


@pytest.mark.anyio
async def test_authenticate_user() -> None:
    """Authentication should return tokens for valid credentials."""
    session = MagicMock()

    service = AuthenticationService(session)

    user = MagicMock()
    user.id = 1
    user.is_active = True
    user.hashed_password = "hashed-password"

    with (
        patch.object(
            service.repository,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ),
        patch(
            "app.services.auth_service.verify_password",
            return_value=True,
        ),
        patch(
            "app.services.auth_service.create_access_token",
            return_value="access-token",
        ),
        patch(
            "app.services.auth_service.create_refresh_token",
            return_value="refresh-token",
        ),
    ):
        result = await service.authenticate(
            "user@example.com",
            "StrongPassword123!",
        )

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"


@pytest.mark.anyio
async def test_authenticate_invalid_password() -> None:
    """Authentication should reject an invalid password."""
    session = MagicMock()

    service = AuthenticationService(session)

    user = MagicMock()
    user.is_active = True
    user.hashed_password = "hashed-password"

    with (
        patch.object(
            service.repository,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ),
        patch(
            "app.services.auth_service.verify_password",
            return_value=False,
        ),
    ):
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.authenticate(
                "user@example.com",
                "WrongPassword123!",
            )
