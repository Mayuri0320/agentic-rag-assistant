"""Tests for health endpoint."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    """Health endpoint should return a successful response."""
    with patch(
        "app.api.v1.endpoints.health.HealthService.check_dependencies",
        new_callable=AsyncMock,
        return_value={
            "database": True,
            "redis": True,
        },
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] is True
    assert data["redis"] is True
