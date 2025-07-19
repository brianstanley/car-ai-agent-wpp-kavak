"""
Chat session and message schemas.
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""
    id: str
    user_id: str
    agent_id: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None


class ChatSessionCreateRequest(BaseModel):
    """Request schema for creating a chat session."""
    phone_number: str
    agent_id: Optional[str] = None


class MessageResponse(BaseModel):
    """Response schema for chat message."""
    id: str
    role: str
    content: str
    created_at: str


class SessionStatsResponse(BaseModel):
    """Response schema for session statistics."""
    total_messages: int
    user_messages: int
    assistant_messages: int
    system_messages: int
    first_message: Optional[str] = None
    last_message: Optional[str] = None


class SummaryResponse(BaseModel):
    """Response schema for session summary."""
    id: str
    text: str
    created_at: str 