"""Tests for the conversation service."""

from unittest.mock import AsyncMock

import pytest

from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.services.conversation_service import ConversationService


@pytest.fixture
def session() -> AsyncMock:
    """Provide a mocked async database session."""
    return AsyncMock()


@pytest.fixture
def service(session: AsyncMock) -> ConversationService:
    """Provide a conversation service."""
    return ConversationService(session)


@pytest.mark.asyncio
async def test_create_conversation(
    service: ConversationService,
) -> None:
    """Create a conversation for a user."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Test Conversation",
    )

    service._conversation_repository.create = AsyncMock(
        return_value=conversation,
    )

    result = await service.create_conversation(
        user_id=10,
        title="Test Conversation",
    )

    assert result is conversation

    service._conversation_repository.create.assert_awaited_once_with(
        user_id=10,
        title="Test Conversation",
    )


@pytest.mark.asyncio
async def test_get_conversation(
    service: ConversationService,
) -> None:
    """Get a conversation belonging to a user."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Test Conversation",
    )

    service._conversation_repository.get_by_id = AsyncMock(
        return_value=conversation,
    )

    result = await service.get_conversation(
        conversation_id=1,
        user_id=10,
    )

    assert result is conversation

    service._conversation_repository.get_by_id.assert_awaited_once_with(
        conversation_id=1,
        user_id=10,
    )


@pytest.mark.asyncio
async def test_get_conversation_returns_none_for_missing_conversation(
    service: ConversationService,
) -> None:
    """Return None when the conversation does not exist."""
    service._conversation_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    result = await service.get_conversation(
        conversation_id=999,
        user_id=10,
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_conversations(
    service: ConversationService,
) -> None:
    """List conversations belonging to a user."""
    conversations = [
        Conversation(
            id=1,
            user_id=10,
            title="First",
        ),
        Conversation(
            id=2,
            user_id=10,
            title="Second",
        ),
    ]

    service._conversation_repository.list_for_user = AsyncMock(
        return_value=conversations,
    )

    result = await service.list_conversations(user_id=10)

    assert result == conversations

    service._conversation_repository.list_for_user.assert_awaited_once_with(
        user_id=10,
    )


@pytest.mark.asyncio
async def test_update_conversation_title(
    service: ConversationService,
) -> None:
    """Update a conversation title owned by the user."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Old Title",
    )

    service._conversation_repository.get_by_id = AsyncMock(
        return_value=conversation,
    )
    service._conversation_repository.update_title = AsyncMock(
        return_value=conversation,
    )

    result = await service.update_conversation_title(
        conversation_id=1,
        user_id=10,
        title="New Title",
    )

    assert result is conversation

    service._conversation_repository.update_title.assert_awaited_once_with(
        conversation=conversation,
        title="New Title",
    )


@pytest.mark.asyncio
async def test_update_conversation_title_returns_none_for_other_user(
    service: ConversationService,
) -> None:
    """Prevent updating a conversation owned by another user."""
    service._conversation_repository.get_by_id = AsyncMock(
        return_value=None,
    )
    service._conversation_repository.update_title = AsyncMock()

    result = await service.update_conversation_title(
        conversation_id=1,
        user_id=999,
        title="Attempted Update",
    )

    assert result is None
    service._conversation_repository.update_title.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_conversation(
    service: ConversationService,
) -> None:
    """Delete a conversation owned by the user."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Test",
    )

    service._conversation_repository.get_by_id = AsyncMock(
        return_value=conversation,
    )
    service._conversation_repository.delete = AsyncMock()

    result = await service.delete_conversation(
        conversation_id=1,
        user_id=10,
    )

    assert result is True

    service._conversation_repository.delete.assert_awaited_once_with(
        conversation=conversation,
    )


@pytest.mark.asyncio
async def test_delete_conversation_returns_false_for_other_user(
    service: ConversationService,
) -> None:
    """Prevent deleting a conversation owned by another user."""
    service._conversation_repository.get_by_id = AsyncMock(
        return_value=None,
    )
    service._conversation_repository.delete = AsyncMock()

    result = await service.delete_conversation(
        conversation_id=1,
        user_id=999,
    )

    assert result is False
    service._conversation_repository.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_message(
    service: ConversationService,
) -> None:
    """Add a message to a user's conversation."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Test",
    )

    message = Message(
        id=1,
        conversation_id=1,
        role="user",
        content="Hello",
    )

    service._conversation_repository.get_by_id = AsyncMock(
        return_value=conversation,
    )
    service._message_repository.create = AsyncMock(
        return_value=message,
    )

    result = await service.add_message(
        conversation_id=1,
        user_id=10,
        role="user",
        content="Hello",
    )

    assert result is message

    service._message_repository.create.assert_awaited_once_with(
        conversation_id=1,
        role="user",
        content="Hello",
    )


@pytest.mark.asyncio
async def test_add_message_returns_none_for_other_user(
    service: ConversationService,
) -> None:
    """Prevent adding messages to another user's conversation."""
    service._conversation_repository.get_by_id = AsyncMock(
        return_value=None,
    )
    service._message_repository.create = AsyncMock()

    result = await service.add_message(
        conversation_id=1,
        user_id=999,
        role="user",
        content="Unauthorized",
    )

    assert result is None
    service._message_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_messages(
    service: ConversationService,
) -> None:
    """List messages from a user's conversation."""
    conversation = Conversation(
        id=1,
        user_id=10,
        title="Test",
    )

    messages = [
        Message(
            id=1,
            conversation_id=1,
            role="user",
            content="Hello",
        ),
        Message(
            id=2,
            conversation_id=1,
            role="assistant",
            content="Hi there",
        ),
    ]

    service._conversation_repository.get_by_id = AsyncMock(
        return_value=conversation,
    )
    service._message_repository.list_for_conversation = AsyncMock(
        return_value=messages,
    )

    result = await service.list_messages(
        conversation_id=1,
        user_id=10,
    )

    assert result == messages

    service._message_repository.list_for_conversation.assert_awaited_once_with(
        conversation_id=1,
    )


@pytest.mark.asyncio
async def test_list_messages_returns_none_for_other_user(
    service: ConversationService,
) -> None:
    """Prevent reading messages from another user's conversation."""
    service._conversation_repository.get_by_id = AsyncMock(
        return_value=None,
    )
    service._message_repository.list_for_conversation = AsyncMock()

    result = await service.list_messages(
        conversation_id=1,
        user_id=999,
    )

    assert result is None
    service._message_repository.list_for_conversation.assert_not_awaited()
