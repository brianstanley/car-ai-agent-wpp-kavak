from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class SummaryMemory(BaseModel):
    """Model for conversation summaries."""
    id: Optional[UUID] = None
    chat_session_id: UUID
    text: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None