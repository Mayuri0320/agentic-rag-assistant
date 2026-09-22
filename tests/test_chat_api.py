"""Tests for the chat API endpoint."""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.agent.dependencies import get_agent_graph
from app.api.v1.endpoints.chat import get_conversation_service
from app.dependencies.auth import get_current_user
from app.main import app

client = TestClient(app)


def override_current_user() -> MagicMock:
    """Return a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.is_active = True
    return user


def override_agent_graph() -> MagicMock:
    """Return a mock agent graph."""
    graph = MagicMock()

    graph.invoke.return_value = {
        "query": "What is machine learning?",
        "user_id": "1",
        "document_id": None,
        "answer": "Machine learning enables systems to learn from data.",
        "verification_passed": True,
        "verification_reason": "Answer has supporting retrieved context.",
        "retrieval_attempts": 1,
        "retrieved_chunks": [
            {
                "chunk_id": "chunk-1",
                "text": "Machine learning enables systems to learn from data.",
                "metadata": {
                    "user_id": "1",
                    "document_id": "1",
                },
            }
        ],
    }

    return graph


def create_conversation_service_mock(
    *,
    conversation_id: int = 1,
) -> MagicMock:
    """Create a mock conversation service."""
    service = MagicMock()

    conversation = MagicMock()
    conversation.id = conversation_id

    service.create_conversation = AsyncMock(
        return_value=conversation,
    )

    service.get_conversation = AsyncMock(
        return_value=conversation,
    )

    service.list_messages = AsyncMock(
        return_value=[],
    )

    service.add_message = AsyncMock(
        return_value=MagicMock(),
    )

    service.commit = AsyncMock()

    return service


def test_chat_returns_agent_answer() -> None:
    """An authenticated user should receive an agent answer."""
    service = create_conversation_service_mock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={
                "query": "What is machine learning?",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["query"] == "What is machine learning?"
        assert data["answer"] == "Machine learning enables systems to learn from data."
        assert data["conversation_id"] == 1
        assert data["verification_passed"] is True
        assert data["retrieval_attempts"] == 1

        service.create_conversation.assert_awaited_once_with(
            user_id=1,
            title="What is machine learning?",
        )

        assert service.add_message.await_count == 2

        service.add_message.assert_any_await(
            conversation_id=1,
            user_id=1,
            role="user",
            content="What is machine learning?",
        )

        service.add_message.assert_any_await(
            conversation_id=1,
            user_id=1,
            role="assistant",
            content="Machine learning enables systems to learn from data.",
        )

        service.commit.assert_awaited_once()

    finally:
        app.dependency_overrides.clear()


def test_chat_requires_authentication() -> None:
    """Chat should require authentication."""
    response = client.post(
        "/chat",
        json={
            "query": "What is machine learning?",
        },
    )

    assert response.status_code == 401


def test_chat_accepts_document_id() -> None:
    """Chat should accept an optional document identifier."""
    service = create_conversation_service_mock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={
                "query": "What is machine learning?",
                "document_id": 1,
            },
        )

        assert response.status_code == 200
        assert response.json()["document_id"] == 1
        assert response.json()["conversation_id"] == 1

    finally:
        app.dependency_overrides.clear()


def test_chat_accepts_existing_conversation_id() -> None:
    """Chat should accept an existing conversation identifier."""
    service = create_conversation_service_mock(
        conversation_id=5,
    )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={
                "query": "Tell me more.",
                "conversation_id": 5,
            },
        )

        assert response.status_code == 200
        assert response.json()["conversation_id"] == 5

        service.create_conversation.assert_not_awaited()

        service.get_conversation.assert_awaited_once_with(
            conversation_id=5,
            user_id=1,
        )

    finally:
        app.dependency_overrides.clear()


def test_chat_rejects_missing_conversation() -> None:
    """Chat should reject a conversation that the user cannot access."""
    service = create_conversation_service_mock()
    service.get_conversation = AsyncMock(
        return_value=None,
    )

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={
                "query": "Tell me more.",
                "conversation_id": 999,
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found."

        service.add_message.assert_not_awaited()
        service.commit.assert_not_awaited()

    finally:
        app.dependency_overrides.clear()


def test_chat_rejects_blank_query() -> None:
    """Chat should reject a blank query."""
    service = create_conversation_service_mock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph
    app.dependency_overrides[get_conversation_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={
                "query": "",
            },
        )

        assert response.status_code == 422
        service.create_conversation.assert_not_awaited()

    finally:
        app.dependency_overrides.clear()
