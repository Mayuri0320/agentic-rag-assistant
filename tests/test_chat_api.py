"""Tests for the chat API endpoint."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agent.dependencies import get_agent_graph
from app.dependencies.auth import get_current_user
from app.main import app

client = TestClient(app)


async def override_current_user() -> MagicMock:
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


def test_chat_returns_agent_answer() -> None:
    """An authenticated user should receive an agent answer."""
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph

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
        assert (
            data["answer"]
            == "Machine learning enables systems to learn from data."
        )
        assert data["verification_passed"] is True
        assert data["retrieval_attempts"] == 1

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
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph

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

    finally:
        app.dependency_overrides.clear()


def test_chat_rejects_blank_query() -> None:
    """Chat should reject a blank query."""
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_agent_graph] = override_agent_graph

    try:
        response = client.post(
            "/chat",
            json={
                "query": "",
            },
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()