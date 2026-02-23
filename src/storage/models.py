"""Pydantic models for conversation storage."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message within a conversation."""
    id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[str]] = None
    metadata: Optional[dict] = None
    created_at: datetime
    seq: int


class Conversation(BaseModel):
    """A conversation with optional messages."""
    id: str
    title: str
    tab: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = Field(default_factory=list)
