"""Tests for the document repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models.document import Document
from app.repositories.document_repository import DocumentRepository


@pytest.mark.anyio
async def test_get_by_id() -> None:
    """Test retrieving a document by ID and user ID."""
    document = MagicMock(spec=Document)

    result = MagicMock()
    result.scalar_one_or_none.return_value = document

    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    repository = DocumentRepository(session)

    response = await repository.get_by_id(
        document_id=1,
        user_id=10,
    )

    assert response is document
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_list_by_user() -> None:
    """Test listing documents for a user."""
    document_one = MagicMock(spec=Document)
    document_two = MagicMock(spec=Document)

    scalars_result = MagicMock()
    scalars_result.all.return_value = [
        document_one,
        document_two,
    ]

    result = MagicMock()
    result.scalars.return_value = scalars_result

    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    repository = DocumentRepository(session)

    response = await repository.list_by_user(user_id=10)

    assert response == [
        document_one,
        document_two,
    ]
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_create_document() -> None:
    """Test creating a document record."""
    session = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    repository = DocumentRepository(session)

    response = await repository.create(
        user_id=10,
        filename="report.pdf",
        file_type="application/pdf",
        file_size=1024,
        storage_path="data/documents/report.pdf",
    )

    assert isinstance(response, Document)
    assert response.user_id == 10
    assert response.filename == "report.pdf"
    assert response.file_type == "application/pdf"
    assert response.file_size == 1024
    assert response.storage_path == "data/documents/report.pdf"
    assert response.status == "uploaded"

    session.add.assert_called_once_with(response)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(response)


@pytest.mark.anyio
async def test_delete_document() -> None:
    """Test deleting a document record."""
    document = MagicMock(spec=Document)

    session = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    repository = DocumentRepository(session)

    await repository.delete(document)

    session.delete.assert_awaited_once_with(document)
    session.flush.assert_awaited_once()
