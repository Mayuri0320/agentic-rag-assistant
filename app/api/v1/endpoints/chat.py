"""Chat API endpoints."""

from fastapi import APIRouter, Depends
from langgraph.graph.state import CompiledStateGraph

from app.agent.dependencies import get_agent_graph
from app.agent.state import AgentState
from app.db.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_graph: CompiledStateGraph = Depends(get_agent_graph),
) -> ChatResponse:
    """Ask a question using the authenticated user's documents."""

    state = AgentState(
        query=request.query,
        user_id=str(current_user.id),
        document_id=(
            str(request.document_id)
            if request.document_id is not None
            else None
        ),
    )

    result = agent_graph.invoke(state)

    return ChatResponse(
        query=result["query"],
        answer=result.get("answer", ""),
        document_id=request.document_id,
        verification_passed=result.get("verification_passed", False),
        verification_reason=result.get("verification_reason"),
        retrieval_attempts=result.get("retrieval_attempts", 0),
    )