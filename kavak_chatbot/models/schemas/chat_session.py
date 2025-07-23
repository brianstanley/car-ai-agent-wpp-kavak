from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class ChatSession(BaseModel):
    """Model for chat sessions."""
    id: Optional[UUID] = None
    user_id: UUID
    agent_id: Optional[UUID] = None  # References MemAgent
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None