from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class Agent(BaseModel):
    """Model for memory agents."""
    id: Optional[UUID] = None
    instruction: Optional[str] = None
    application_mode: str = "assistant"
    persona_id: Optional[UUID] = None
    tools: Optional[Dict[str, Any]] = None