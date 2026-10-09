"""Repository for code artifact persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.code_artifact import CodeArtifact


class CodeArtifactRepository:
    """Handle database operations for code artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository."""
        self._session = session

    async def create(
        self,
        *,
        conversation_id: int,
        filename: str,
        language: str,
        source_code: str,
    ) -> CodeArtifact:
        """Create a new code artifact."""

        artifact = CodeArtifact(
            conversation_id=conversation_id,
            filename=filename,
            language=language,
            source_code=source_code,
        )

        self._session.add(artifact)

        await self._session.flush()

        return artifact

    async def get_latest_for_conversation(
        self,
        *,
        conversation_id: int,
    ) -> CodeArtifact | None:
        """Return the latest code artifact for a conversation."""

        statement = (
            select(CodeArtifact)
            .where(
                CodeArtifact.conversation_id == conversation_id,
            )
            .order_by(
                CodeArtifact.updated_at.desc(),
                CodeArtifact.id.desc(),
            )
            .limit(1)
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_for_conversation(
        self,
        *,
        conversation_id: int,
    ) -> list[CodeArtifact]:
        """Return all code artifacts for a conversation."""

        statement = (
            select(CodeArtifact)
            .where(
                CodeArtifact.conversation_id == conversation_id,
            )
            .order_by(
                CodeArtifact.created_at.asc(),
                CodeArtifact.id.asc(),
            )
        )

        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def get_by_id(
        self,
        *,
        artifact_id: int,
        conversation_id: int,
    ) -> CodeArtifact | None:
        """Return an artifact belonging to a conversation."""

        statement = select(CodeArtifact).where(
            CodeArtifact.id == artifact_id,
            CodeArtifact.conversation_id == conversation_id,
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()
