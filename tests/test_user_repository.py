"""Tests for the user repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.user_repository import UserRepository


@pytest.mark.anyio
async def test_get_by_email() -> None:
    """Repository should return a user by email."""
    session = MagicMock()
    session.execute = AsyncMock()

    user = MagicMock()
    user.email = "user@example.com"

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    repository = UserRepository(session)

    found_user = await repository.get_by_email("user@example.com")

    assert found_user is user
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_get_by_id() -> None:
    """Repository should return a user by ID."""
    session = MagicMock()
    session.execute = AsyncMock()

    user = MagicMock()
    user.id = 1

    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    repository = UserRepository(session)

    found_user = await repository.get_by_id(1)

    assert found_user is user
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_create_user() -> None:
    """Repository should create and persist a user."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    repository = UserRepository(session)

    user = await repository.create(
        email="user@example.com",
        hashed_password="hashed-password",
    )

    assert user.email == "user@example.com"
    assert user.hashed_password == "hashed-password"

    session.add.assert_called_once_with(user)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(user)
