"""Repository for conversation persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation


class ConversationRepository:
    """Provide database operations for conversations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository."""
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a conversation for a user."""
        conversation = Conversation(
            user_id=user_id,
            title=title.strip() or "New Conversation",
        )

        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)

        return conversation

    async def get_by_id(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> Conversation | None:
        """Get a conversation belonging to a specific user."""
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: int,
    ) -> list[Conversation]:
        """Return all conversations belonging to a user."""
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def update_title(
        self,
        *,
        conversation: Conversation,
        title: str,
    ) -> Conversation:
        """Update a conversation title."""
        cleaned_title = title.strip()

        if not cleaned_title:
            raise ValueError("Conversation title cannot be empty.")

        conversation.title = cleaned_title

        await self._session.flush()
        await self._session.refresh(conversation)

        return conversation

    async def delete(
        self,
        *,
        conversation: Conversation,
    ) -> None:
        """Delete a conversation."""
        await self._session.delete(conversation)
        await self._session.flush()
