"""Tests for document API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app

client = TestClient(app)


async def override_current_user() -> MagicMock:
    """Return a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.is_active = True
    return user


def test_upload_document() -> None:
    """An authenticated user should be able to upload a document."""
    app.dependency_overrides[get_current_user] = override_current_user

    document = MagicMock()
    document.id = 1
    document.filename = "report.pdf"
    document.file_type = "application/pdf"
    document.file_size = 1024
    document.storage_path = "data/documents/report.pdf"
    document.status = "uploaded"

    try:
        with patch(
            "app.api.v1.endpoints.documents.DocumentService",
        ) as service_class:
            service = service_class.return_value
            service.create_document = AsyncMock(return_value=document)

            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "report.pdf",
                        b"%PDF-test-content",
                        "application/pdf",
                    )
                },
            )

        assert response.status_code == 201
        assert response.json()["filename"] == "report.pdf"
    finally:
        app.dependency_overrides.clear()


def test_upload_requires_authentication() -> None:
    """Uploading a document should require authentication."""
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "report.pdf",
                b"%PDF-test-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 401


def test_list_documents() -> None:
    """An authenticated user should receive their documents."""
    app.dependency_overrides[get_current_user] = override_current_user

    document = MagicMock()
    document.id = 1
    document.filename = "report.pdf"
    document.file_type = "application/pdf"
    document.file_size = 1024
    document.storage_path = "data/documents/report.pdf"
    document.status = "uploaded"

    try:
        with patch(
            "app.api.v1.endpoints.documents.DocumentService",
        ) as service_class:
            service = service_class.return_value
            service.list_documents = AsyncMock(return_value=[document])

            response = client.get("/documents")

        assert response.status_code == 200
        assert len(response.json()["documents"]) == 1
        assert response.json()["documents"][0]["filename"] == "report.pdf"
    finally:
        app.dependency_overrides.clear()


def test_get_document() -> None:
    """An authenticated user should be able to retrieve a document."""
    app.dependency_overrides[get_current_user] = override_current_user

    document = MagicMock()
    document.id = 1
    document.filename = "report.pdf"
    document.file_type = "application/pdf"
    document.file_size = 1024
    document.storage_path = "data/documents/report.pdf"
    document.status = "uploaded"

    try:
        with patch(
            "app.api.v1.endpoints.documents.DocumentService",
        ) as service_class:
            service = service_class.return_value
            service.get_document = AsyncMock(return_value=document)

            response = client.get("/documents/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
    finally:
        app.dependency_overrides.clear()


def test_get_document_not_found() -> None:
    """A missing document should return 404."""
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        with patch(
            "app.api.v1.endpoints.documents.DocumentService",
        ) as service_class:
            service = service_class.return_value
            service.get_document = AsyncMock(
                side_effect=ValueError("Document not found"),
            )

            response = client.get("/documents/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"
    finally:
        app.dependency_overrides.clear()


def test_delete_document() -> None:
    """An authenticated user should be able to delete a document."""
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        with patch(
            "app.api.v1.endpoints.documents.DocumentService",
        ) as service_class:
            service = service_class.return_value
            service.delete_document = AsyncMock()

            response = client.delete("/documents/1")

        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
