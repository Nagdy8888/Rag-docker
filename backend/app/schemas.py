"""Pydantic models for API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Chat ---
class ChatSessionCreate(BaseModel):
    """Request to create a new chat session."""

    title: str = "New Chat"


class ChatSessionResponse(BaseModel):
    """Chat session as returned by the API."""

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    """Request to send a message (streaming response)."""

    session_id: UUID
    content: str = Field(..., min_length=1)


class SourceRefResponse(BaseModel):
    """A source reference (Phase 4): filename, chunk index, snippet."""

    filename: str = ""
    chunk_index: int | None = None
    snippet: str | None = None


class ChatMessageResponse(BaseModel):
    """A single chat message."""

    id: UUID
    session_id: UUID
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
    sources: list[SourceRefResponse] = []  # Phase 4: document refs used for this message


class ChatSessionWithMessages(ChatSessionResponse):
    """Chat session with its messages."""

    messages: list[ChatMessageResponse] = []
