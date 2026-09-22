"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.dependencies import get_agent_graph
from app.agent.state import AgentState, ConversationMessage
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_conversation_service(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationService:
    """Provide the conversation service."""
    return ConversationService(session)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_graph: CompiledStateGraph = Depends(get_agent_graph),
    conversation_service: ConversationService = Depends(
        get_conversation_service,
    ),
) -> ChatResponse:
    """Process a chat request with persistent conversation memory."""

    user_id = current_user.id

    if request.conversation_id is None:
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            title=request.query[:100],
        )
    else:
        existing_conversation = await conversation_service.get_conversation(
            conversation_id=request.conversation_id,
            user_id=user_id,
        )

        if existing_conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        conversation = existing_conversation

    # Load previous messages BEFORE adding the current user message.
    previous_messages = await conversation_service.list_messages(
        conversation_id=conversation.id,
        user_id=user_id,
    )

    if previous_messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    conversation_history = [
        ConversationMessage(
            role=message.role,
            content=message.content,
        )
        for message in previous_messages
    ]

    # Persist the current user message.
    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=request.query,
    )

    state = AgentState(
        query=request.query,
        user_id=str(user_id),
        document_id=(
            str(request.document_id) if request.document_id is not None else None
        ),
        conversation_history=conversation_history,
    )

    result = agent_graph.invoke(state)

    answer = result.get("answer", "")

    # Persist the generated assistant response.
    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content=answer,
    )

    await conversation_service.commit()

    return ChatResponse(
        query=result["query"],
        answer=answer,
        conversation_id=conversation.id,
        document_id=request.document_id,
        verification_passed=result.get("verification_passed", False),
        verification_reason=result.get("verification_reason"),
        retrieval_attempts=result.get("retrieval_attempts", 0),
    )
