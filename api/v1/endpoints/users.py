"""
User management endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID

from services.user_service import UserService
from models.schemas.user import User, UserCreateRequest, UserUpdateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
async def get_users() -> List[UserResponse]:
    """Get all users."""
    try:
        user_service = UserService()
        users = user_service.get_all_users()
        
        return [
            UserResponse(
                id=str(user.id),
                phone_number=user.phone_number,
                name=user.name,
                preferences=user.preferences,
                created_at=user.created_at.isoformat() if user.created_at else "",
                updated_at=None  # User schema doesn't have updated_at field
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    """Get a specific user by ID."""
    try:
        user_service = UserService()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            preferences=user.preferences,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=None  # User schema doesn't have updated_at field
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest) -> UserResponse:
    """Create a new user."""
    try:
        user_service = UserService()
        user = user_service.get_or_create_user(user_data.phone_number)
        
        return UserResponse(
            id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            preferences=user.preferences,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=None  # User schema doesn't have updated_at field
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdateRequest) -> UserResponse:
    """Update a user."""
    try:
        user_service = UserService()
        user = user_service.update_user(
            user_id=user_id,
            name=user_data.name,
            preferences=user_data.preferences
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=str(user.id),
            phone_number=user.phone_number,
            name=user.name,
            preferences=user.preferences,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=None  # User schema doesn't have updated_at field
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: str) -> Dict[str, str]:
    """Delete a user."""
    try:
        user_service = UserService()
        success = user_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 