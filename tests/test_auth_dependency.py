"""Tests for JWT authentication dependency."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_me_without_token() -> None:
    """Requests without credentials should be rejected."""
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_auth_me_invalid_token() -> None:
    """Invalid JWTs should be rejected."""
    with patch(
        "app.dependencies.auth.decode_token",
        side_effect=ValueError("Invalid token"),
    ):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_auth_me_refresh_token() -> None:
    """Refresh tokens should not authenticate protected endpoints."""
    with patch(
        "app.dependencies.auth.decode_token",
        return_value={
            "sub": "1",
            "type": "refresh",
        },
    ):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer refresh-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Access token required"


def test_auth_me_valid_access_token() -> None:
    """A valid access token should return the current user."""
    user = MagicMock()
    user.id = 1
    user.email = "user@example.com"
    user.is_active = True

    mock_repository = MagicMock()
    mock_repository.get_by_id = AsyncMock(return_value=user)

    with (
        patch(
            "app.dependencies.auth.decode_token",
            return_value={
                "sub": "1",
                "type": "access",
            },
        ),
        patch(
            "app.dependencies.auth.UserRepository",
            return_value=mock_repository,
        ),
    ):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer access-token"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["email"] == "user@example.com"
    assert data["is_active"] is True
