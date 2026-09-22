"""State definitions for the agentic RAG workflow."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ConversationMessage:
    """Represent a previous conversation message."""

    role: str
    content: str


@dataclass(slots=True)
class AgentState:
    """Shared state passed between nodes in the agentic RAG workflow."""

    query: str
    user_id: str

    document_id: str | None = None

    conversation_history: list[ConversationMessage] = field(
        default_factory=list,
    )

    retrieved_chunks: list[dict[str, Any]] = field(default_factory=list)

    answer: str | None = None

    verification_passed: bool = False

    verification_reason: str | None = None

    retrieval_attempts: int = 0

    error: str | None = None
