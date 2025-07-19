"""
Kavak information schemas.
"""

from typing import List, Optional
from pydantic import BaseModel


class KavakInfoCreateRequest(BaseModel):
    """Request schema for creating Kavak info."""
    text: str
    title: Optional[str] = None
    metadata: Optional[List[str]] = None


class KavakInfoResponse(BaseModel):
    """Response schema for Kavak info."""
    id: str
    text: str
    title: Optional[str] = None
    metadata: Optional[List[str]] = None
    created_at: str
    updated_at: Optional[str] = None


class KavakInfoSearchRequest(BaseModel):
    """Request schema for searching Kavak info."""
    query: str
    limit: Optional[int] = 5 