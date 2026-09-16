"""Schemas for the chat API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for asking a question."""

    query: str = Field(min_length=1, max_length=4000)
    document_id: int | None = None


class ChatResponse(BaseModel):
    """Response returned by the agent."""

    query: str
    answer: str
    document_id: int | None = None
    verification_passed: bool
    verification_reason: str | None = None
    retrieval_attempts: int