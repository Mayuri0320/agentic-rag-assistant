"""Tests for health service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.health_service import HealthService


@pytest.mark.anyio
async def test_health_dependencies() -> None:
    """Health dependencies should return healthy status."""
    service = HealthService()

    with (
        patch.object(
            service,
            "check_database",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch.object(
            service,
            "check_redis",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        result = await service.check_dependencies()

    assert result == {
        "database": True,
        "redis": True,
    }
