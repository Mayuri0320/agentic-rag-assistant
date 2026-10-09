"""Chat API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.dependencies import get_agent_graph
from app.agent.state import AgentState, CodeArtifact, ConversationMessage
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

    # ------------------------------------------------------------------
    # 1. Get or create the conversation.
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 2. Load previous conversation messages.
    #
    # The current user message is intentionally NOT included here.
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 3. Load the latest code artifact for this conversation.
    #
    # This allows follow-up requests such as:
    #
    # "Now convert that to C++."
    # "Fix the sorting logic."
    # "Add error handling."
    # "Explain this function."
    # ------------------------------------------------------------------
    latest_artifact = await conversation_service.get_latest_code_artifact(
        conversation_id=conversation.id,
        user_id=user_id,
    )

    code_artifact = None

    if latest_artifact is not None:
        code_artifact = CodeArtifact(
            filename=latest_artifact.filename,
            language=latest_artifact.language,
            source_code=latest_artifact.source_code,
        )

    # ------------------------------------------------------------------
    # 4. Persist the current user message.
    # ------------------------------------------------------------------
    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=request.query,
    )

    # ------------------------------------------------------------------
    # 5. Build the agent state.
    # ------------------------------------------------------------------
    state = AgentState(
        query=request.query,
        user_id=str(user_id),
        document_id=(
            str(request.document_id) if request.document_id is not None else None
        ),
        conversation_history=conversation_history,
        code_artifact=code_artifact,
    )

    # ------------------------------------------------------------------
    # 6. Run the agent graph.
    # ------------------------------------------------------------------
    result = agent_graph.invoke(state)

    answer = result.get("answer", "")

    # ------------------------------------------------------------------
    # 7. Persist a newly generated code artifact.
    #
    # The coding node places the generated code in
    # state.generated_code_artifact. Saving it here makes the newly
    # generated code available to the next message in this conversation.
    # ------------------------------------------------------------------
    generated_artifact = result.get("generated_code_artifact")

    if generated_artifact is not None:
        await conversation_service.add_code_artifact(
            conversation_id=conversation.id,
            user_id=user_id,
            filename=generated_artifact.filename,
            language=generated_artifact.language,
            source_code=generated_artifact.source_code,
        )

    # ------------------------------------------------------------------
    # 8. Persist the generated assistant response.
    # ------------------------------------------------------------------
    await conversation_service.add_message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content=answer,
    )

    await conversation_service.commit()

    # ------------------------------------------------------------------
    # 9. Return the response.
    # ------------------------------------------------------------------
    return ChatResponse(
        query=result["query"],
        answer=answer,
        conversation_id=conversation.id,
        document_id=request.document_id,
        verification_passed=result.get("verification_passed", False),
        verification_reason=result.get("verification_reason"),
        retrieval_attempts=result.get("retrieval_attempts", 0),
    )
