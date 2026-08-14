"""Tests for refresh token endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_refresh_token_success() -> None:
    """A valid refresh token should create a new access token."""
    user = MagicMock()
    user.id = 1
    user.is_active = True

    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=user)

    with (
        patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "1", "type": "refresh"},
        ),
        patch(
            "app.services.auth_service.create_access_token",
            return_value="new-access-token",
        ),
        patch(
            "app.services.auth_service.UserRepository",
            return_value=repository,
        ),
    ):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] == "new-access-token"
    assert data["refresh_token"] == "valid-refresh-token"
    assert data["token_type"] == "bearer"


def test_refresh_rejects_access_token() -> None:
    """An access token must not be accepted as a refresh token."""
    with patch(
        "app.services.auth_service.decode_token",
        return_value={"sub": "1", "type": "access"},
    ):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "access-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token required"


def test_refresh_rejects_invalid_token() -> None:
    """An invalid refresh token should be rejected."""
    with patch(
        "app.services.auth_service.decode_token",
        side_effect=ValueError("Invalid token"),
    ):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


def test_refresh_rejects_inactive_user() -> None:
    """An inactive user cannot refresh an access token."""
    user = MagicMock()
    user.id = 1
    user.is_active = False

    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=user)

    with (
        patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "1", "type": "refresh"},
        ),
        patch(
            "app.services.auth_service.UserRepository",
            return_value=repository,
        ),
    ):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "User not found or inactive"
