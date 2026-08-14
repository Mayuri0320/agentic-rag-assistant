"""Tests for Redis service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.redis_service import check_redis_connection


@pytest.mark.anyio
async def test_redis_connection() -> None:
    """Redis connection check should return True when Redis responds."""
    with patch(
        "app.services.redis_service.redis_client.ping",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await check_redis_connection()

    assert result is True
