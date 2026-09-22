"""Schemas for conversation APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Represent a conversation message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    """Represent a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Represent a list of conversations."""

    conversations: list[ConversationResponse]


class ConversationDetailResponse(BaseModel):
    """Represent a conversation with its messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]
