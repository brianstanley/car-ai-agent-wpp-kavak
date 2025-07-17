from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    """Model for users."""
    id: Optional[UUID] = None
    phone_number: str
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None