"""Tests for authentication API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_endpoint() -> None:
    """Registration endpoint should return authentication tokens."""
    mock_service = MagicMock()
    mock_service.register = AsyncMock(
        return_value={
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
        }
    )

    with patch(
        "app.api.v1.endpoints.auth.AuthenticationService",
        return_value=mock_service,
    ):
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["access_token"] == "access-token"
    assert data["refresh_token"] == "refresh-token"
    assert data["token_type"] == "bearer"


def test_login_endpoint() -> None:
    """Login endpoint should return authentication tokens."""
    mock_service = MagicMock()
    mock_service.authenticate = AsyncMock(
        return_value={
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
        }
    )

    with patch(
        "app.api.v1.endpoints.auth.AuthenticationService",
        return_value=mock_service,
    ):
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] == "access-token"
    assert data["refresh_token"] == "refresh-token"
    assert data["token_type"] == "bearer"


def test_register_invalid_email() -> None:
    """Registration should reject an invalid email."""
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password() -> None:
    """Registration should reject a short password."""
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422
