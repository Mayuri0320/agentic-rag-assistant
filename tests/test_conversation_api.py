"""Tests for conversation API endpoints."""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.v1.endpoints.conversations import get_conversation_service
from app.dependencies.auth import get_current_user
from app.main import app

client = TestClient(app)


def override_current_user() -> MagicMock:
    """Return a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.is_active = True
    return user


def create_conversation(
    *,
    conversation_id: int,
    title: str,
) -> MagicMock:
    """Create a mock conversation."""
    conversation = MagicMock()
    conversation.id = conversation_id
    conversation.title = title
    conversation.created_at = MagicMock()
    conversation.updated_at = MagicMock()
    return conversation


def create_message(
    *,
    message_id: int,
    role: str,
    content: str,
) -> MagicMock:
    """Create a mock conversation message."""
    message = MagicMock()
    message.id = message_id
    message.role = role
    message.content = content
    message.created_at = MagicMock()
    return message


def create_service_mock() -> MagicMock:
    """Create a mocked conversation service."""
    service = MagicMock()

    service.list_conversations = AsyncMock(
        return_value=[
            create_conversation(
                conversation_id=1,
                title="Machine Learning",
            ),
            create_conversation(
                conversation_id=2,
                title="Deep Learning",
            ),
        ],
    )

    service.get_conversation = AsyncMock(
        return_value=create_conversation(
            conversation_id=1,
            title="Machine Learning",
        ),
    )

    service.list_messages = AsyncMock(
        return_value=[
            create_message(
                message_id=1,
                role="user",
                content="What is machine learning?",
            ),
            create_message(
                message_id=2,
                role="assistant",
                content="Machine learning enables systems to learn from data.",
            ),
        ],
    )

    return service


def test_list_conversations() -> None:
    """An authenticated user should receive their conversations."""
    service = create_service_mock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.get("/conversations")

        assert response.status_code == 200

        data = response.json()

        assert len(data["conversations"]) == 2
        assert data["conversations"][0]["id"] == 1
        assert data["conversations"][0]["title"] == "Machine Learning"
        assert data["conversations"][1]["id"] == 2
        assert data["conversations"][1]["title"] == "Deep Learning"

        service.list_conversations.assert_awaited_once_with(
            user_id=1,
        )

    finally:
        app.dependency_overrides.clear()


def test_get_conversation() -> None:
    """An authenticated user should receive a conversation with messages."""
    service = create_service_mock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.get("/conversations/1")

        assert response.status_code == 200

        data = response.json()

        assert data["conversation"]["id"] == 1
        assert data["conversation"]["title"] == "Machine Learning"

        assert len(data["messages"]) == 2

        assert data["messages"][0]["id"] == 1
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == ("What is machine learning?")

        assert data["messages"][1]["id"] == 2
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == (
            "Machine learning enables systems to learn from data."
        )

        service.get_conversation.assert_awaited_once_with(
            conversation_id=1,
            user_id=1,
        )

        service.list_messages.assert_awaited_once_with(
            conversation_id=1,
            user_id=1,
        )

    finally:
        app.dependency_overrides.clear()


def test_get_conversation_not_found() -> None:
    """An inaccessible conversation should return 404."""
    service = create_service_mock()

    service.get_conversation = AsyncMock(
        return_value=None,
    )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.get("/conversations/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found."

        service.list_messages.assert_not_awaited()

    finally:
        app.dependency_overrides.clear()


def test_conversations_require_authentication() -> None:
    """Conversation endpoints should require authentication."""
    response = client.get("/conversations")

    assert response.status_code == 401
