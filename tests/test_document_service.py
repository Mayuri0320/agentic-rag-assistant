"""Tests for the document service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models.document import Document
from app.services.document_service import DocumentService


def create_service() -> DocumentService:
    """Create a document service with mocked dependencies."""
    service = DocumentService(
        MagicMock(),
        MagicMock(),
    )
    return service


def test_validate_pdf() -> None:
    """A valid PDF should pass validation."""
    service = create_service()

    service.validate_file(
        filename="report.pdf",
        file_size=1024,
    )


def test_validate_txt() -> None:
    """A valid text file should pass validation."""
    service = create_service()

    service.validate_file(
        filename="notes.txt",
        file_size=500,
    )


def test_reject_unsupported_file_type() -> None:
    """Unsupported file types should be rejected."""
    service = create_service()

    with pytest.raises(ValueError, match="Unsupported file type"):
        service.validate_file(
            filename="malware.exe",
            file_size=1024,
        )


def test_reject_empty_file() -> None:
    """Empty files should be rejected."""
    service = create_service()

    with pytest.raises(ValueError, match="File cannot be empty"):
        service.validate_file(
            filename="empty.pdf",
            file_size=0,
        )


def test_reject_file_too_large() -> None:
    """Files larger than 10 MB should be rejected."""
    service = create_service()

    with pytest.raises(ValueError, match="10 MB"):
        service.validate_file(
            filename="large.pdf",
            file_size=11 * 1024 * 1024,
        )


@pytest.mark.anyio
async def test_create_document() -> None:
    """A valid document should be stored and created."""
    document = MagicMock(spec=Document)

    repository = MagicMock()
    repository.create = AsyncMock(return_value=document)

    storage = MagicMock()
    storage.save.return_value = "data/documents/report.pdf"

    service = DocumentService(
        MagicMock(),
        storage,
    )
    service.repository = repository

    response = await service.create_document(
        user_id=1,
        filename="report.pdf",
        file_type="application/pdf",
        file_size=1024,
        content=b"test document",
    )

    assert response is document

    storage.save.assert_called_once_with(
        filename="report.pdf",
        content=b"test document",
    )

    repository.create.assert_awaited_once_with(
        user_id=1,
        filename="report.pdf",
        file_type="application/pdf",
        file_size=1024,
        storage_path="data/documents/report.pdf",
    )


@pytest.mark.anyio
async def test_create_document_rolls_back_storage_on_database_error() -> None:
    """Stored files should be deleted if database creation fails."""
    repository = MagicMock()
    repository.create = AsyncMock(
        side_effect=RuntimeError("database error"),
    )

    storage = MagicMock()
    storage.save.return_value = "data/documents/report.pdf"

    service = DocumentService(
        MagicMock(),
        storage,
    )
    service.repository = repository

    with pytest.raises(RuntimeError, match="database error"):
        await service.create_document(
            user_id=1,
            filename="report.pdf",
            file_type="application/pdf",
            file_size=1024,
            content=b"test document",
        )

    storage.save.assert_called_once_with(
        filename="report.pdf",
        content=b"test document",
    )
    storage.delete.assert_called_once_with(
        "data/documents/report.pdf",
    )


@pytest.mark.anyio
async def test_get_document() -> None:
    """A document belonging to the user should be returned."""
    document = MagicMock(spec=Document)

    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=document)

    service = DocumentService(
        MagicMock(),
        MagicMock(),
    )
    service.repository = repository

    response = await service.get_document(
        document_id=5,
        user_id=1,
    )

    assert response is document

    repository.get_by_id.assert_awaited_once_with(
        document_id=5,
        user_id=1,
    )


@pytest.mark.anyio
async def test_get_document_not_found() -> None:
    """A missing document should raise an error."""
    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=None)

    service = DocumentService(
        MagicMock(),
        MagicMock(),
    )
    service.repository = repository

    with pytest.raises(ValueError, match="Document not found"):
        await service.get_document(
            document_id=999,
            user_id=1,
        )


@pytest.mark.anyio
async def test_list_documents() -> None:
    """Documents should be listed for the current user."""
    documents = [
        MagicMock(spec=Document),
        MagicMock(spec=Document),
    ]

    repository = MagicMock()
    repository.list_by_user = AsyncMock(return_value=documents)

    service = DocumentService(
        MagicMock(),
        MagicMock(),
    )
    service.repository = repository

    response = await service.list_documents(user_id=1)

    assert response == documents

    repository.list_by_user.assert_awaited_once_with(1)


@pytest.mark.anyio
async def test_delete_document() -> None:
    """A user's document should be deleted."""
    document = MagicMock(spec=Document)
    document.storage_path = "data/documents/report.pdf"

    repository = MagicMock()
    repository.get_by_id = AsyncMock(return_value=document)
    repository.delete = AsyncMock()

    storage = MagicMock()

    service = DocumentService(
        MagicMock(),
        storage,
    )
    service.repository = repository

    await service.delete_document(
        document_id=5,
        user_id=1,
    )

    repository.get_by_id.assert_awaited_once_with(
        document_id=5,
        user_id=1,
    )
    repository.delete.assert_awaited_once_with(document)
    storage.delete.assert_called_once_with(
        "data/documents/report.pdf",
    )
