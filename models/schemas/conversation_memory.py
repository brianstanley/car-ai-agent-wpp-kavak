from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class ConversationMemory(BaseModel):
    """Model for conversation memory entries."""
    id: Optional[UUID] = None
    chat_session_id: UUID
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    created_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    embedded: bool = False
