"""Repository for conversation message persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message


class MessageRepository:
    """Provide database operations for conversation messages."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository."""
        self._session = session

    async def create(
        self,
        *,
        conversation_id: int,
        role: str,
        content: str,
    ) -> Message:
        """Create a message in a conversation."""
        cleaned_role = role.strip().lower()
        cleaned_content = content.strip()

        if not cleaned_role:
            raise ValueError("Message role cannot be empty.")

        if not cleaned_content:
            raise ValueError("Message content cannot be empty.")

        message = Message(
            conversation_id=conversation_id,
            role=cleaned_role,
            content=cleaned_content,
        )

        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)

        return message

    async def list_for_conversation(
        self,
        *,
        conversation_id: int,
    ) -> list[Message]:
        """Return messages ordered from oldest to newest."""
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        *,
        message_id: int,
        conversation_id: int,
    ) -> Message | None:
        """Get a message belonging to a specific conversation."""
        statement = select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
