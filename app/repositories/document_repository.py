"""Document repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document


class DocumentRepository:
    """Handle database operations for documents."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository."""
        self.session = session

    async def get_by_id(
        self,
        document_id: int,
        user_id: int,
    ) -> Document | None:
        """Get a document belonging to a specific user."""
        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
    ) -> list[Document]:
        """List documents belonging to a specific user."""
        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        status: str = "uploaded",
    ) -> Document:
        """Create a document record."""
        document = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            status=status,
        )

        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)

        return document

    async def delete(
        self,
        document: Document,
    ) -> None:
        """Delete a document."""
        await self.session.delete(document)
        await self.session.flush()