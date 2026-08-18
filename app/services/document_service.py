"""Document service."""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.storage.document_storage import DocumentStorage


class DocumentService:
    """Handle document business logic."""

    ALLOWED_FILE_TYPES = {
        ".pdf",
        ".txt",
        ".docx",
        ".md",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        session: AsyncSession,
        storage: DocumentStorage,
    ) -> None:
        """Initialize the document service."""
        self.repository = DocumentRepository(session)
        self.storage = storage

    def validate_file(
        self,
        filename: str,
        file_size: int,
    ) -> None:
        """Validate document filename and size."""
        extension = Path(filename).suffix.lower()

        if extension not in self.ALLOWED_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {extension or 'unknown'}"
            )

        if file_size <= 0:
            raise ValueError("File cannot be empty")

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError("File size exceeds the 10 MB limit")

    async def create_document(
        self,
        user_id: int,
        filename: str,
        file_type: str,
        file_size: int,
        content: bytes,
    ) -> Document:
        """Validate, store, and create a document record."""
        self.validate_file(
            filename=filename,
            file_size=file_size,
        )

        storage_path = self.storage.save(
            filename=filename,
            content=content,
        )

        try:
            return await self.repository.create(
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                storage_path=storage_path,
            )
        except Exception:
            self.storage.delete(storage_path)
            raise

    async def get_document(
        self,
        document_id: int,
        user_id: int,
    ) -> Document:
        """Get a document belonging to the current user."""
        document = await self.repository.get_by_id(
            document_id=document_id,
            user_id=user_id,
        )

        if document is None:
            raise ValueError("Document not found")

        return document

    async def list_documents(
        self,
        user_id: int,
    ) -> list[Document]:
        """List documents belonging to the current user."""
        return await self.repository.list_by_user(user_id)

    async def delete_document(
        self,
        document_id: int,
        user_id: int,
    ) -> None:
        """Delete a document belonging to the current user."""
        document = await self.get_document(
            document_id=document_id,
            user_id=user_id,
        )

        await self.repository.delete(document)

        self.storage.delete(document.storage_path)