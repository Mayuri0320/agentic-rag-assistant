"""Service for conversation and message persistence."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.message import MessageRepository


class ConversationService:
    """Manage conversations and their messages."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the conversation service."""
        self._conversation_repository = ConversationRepository(session)
        self._message_repository = MessageRepository(session)

    async def create_conversation(
        self,
        *,
        user_id: int,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a new conversation for a user."""
        return await self._conversation_repository.create(
            user_id=user_id,
            title=title,
        )

    async def get_conversation(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> Conversation | None:
        """Get a conversation owned by the specified user."""
        return await self._conversation_repository.get_by_id(
            conversation_id=conversation_id,
            user_id=user_id,
        )

    async def list_conversations(
        self,
        *,
        user_id: int,
    ) -> list[Conversation]:
        """List all conversations belonging to a user."""
        return await self._conversation_repository.list_for_user(
            user_id=user_id,
        )

    async def update_conversation_title(
        self,
        *,
        conversation_id: int,
        user_id: int,
        title: str,
    ) -> Conversation | None:
        """Update a conversation title if the user owns it."""
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return None

        return await self._conversation_repository.update_title(
            conversation=conversation,
            title=title,
        )

    async def delete_conversation(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> bool:
        """Delete a conversation if the user owns it."""
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return False

        await self._conversation_repository.delete(
            conversation=conversation,
        )
        return True

    async def add_message(
        self,
        *,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
    ) -> Message | None:
        """Add a message to a conversation owned by the user."""
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return None

        return await self._message_repository.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

    async def list_messages(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> list[Message] | None:
        """List messages for a conversation owned by the user."""
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            return None

        return await self._message_repository.list_for_conversation(
            conversation_id=conversation_id,
        )

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._conversation_repository.commit()
