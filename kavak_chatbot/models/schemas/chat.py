"""
Chat session and message schemas.
"""

from typing import Optional
from pydantic import BaseModel

from .user import User
from .chat_session import ChatSession

class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    agent_id: Optional[str] = None
    started_at: str
    ended_at: Optional[str] = None


class ChatSessionCreateRequest(BaseModel):
    phone_number: str
    agent_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class SessionStatsResponse(BaseModel):
    total_messages: int
    user_messages: int
    assistant_messages: int
    system_messages: int
    first_message: Optional[str] = None
    last_message: Optional[str] = None


class SummaryResponse(BaseModel):
    id: str
    text: str
    created_at: str


class InitializeChatResponse(BaseModel):
    user: User
    session: ChatSession
    session_type: str
    phone_number: str