from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    """Model for users."""
    id: Optional[UUID] = None
    phone_number: str
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""
    phone_number: str
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Response schema for user."""
    id: str
    phone_number: str
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None