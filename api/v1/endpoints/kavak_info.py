"""
Kavak information management endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.kavak_info_service import KavakInfoService
from models.schemas.kavak_info import (
    KavakInfoCreateRequest,
    KavakInfoResponse,
    KavakInfoSearchRequest
)

router = APIRouter(prefix="/kavak-info", tags=["Kavak Info"])


def _convert_db_to_response(record) -> KavakInfoResponse:
    """Convert database record to response model."""
    return KavakInfoResponse(
        id=str(record.id),
        text=str(record.text),
        title=str(record.title) if record.title else None,
        metadata=list(record.meta) if record.meta else None,
        created_at=record.created_at.isoformat() if record.created_at else "",
        updated_at=record.updated_at.isoformat() if record.updated_at else None
    )


@router.get("/", response_model=List[KavakInfoResponse])
async def get_all_kavak_info() -> List[KavakInfoResponse]:
    """Get all Kavak information records."""
    try:
        kavak_service = KavakInfoService()
        records = kavak_service.get_all_kavak_info()
        
        return [_convert_db_to_response(record) for record in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=KavakInfoResponse)
async def create_kavak_info(info_data: KavakInfoCreateRequest) -> KavakInfoResponse:
    """Create a new Kavak information record."""
    try:
        kavak_service = KavakInfoService()
        success = kavak_service.create_kavak_info_with_embedding(
            text=info_data.text,
            title=info_data.title,
            metadata=info_data.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create Kavak info record")
        
        # Note: The service doesn't return the created record, so we can't return the full response
        # You might want to modify the service to return the created record
        raise HTTPException(status_code=501, detail="Service needs to be modified to return created record")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[KavakInfoResponse])
async def search_kavak_info(search_data: KavakInfoSearchRequest) -> List[KavakInfoResponse]:
    """Search for similar Kavak information using semantic search."""
    try:
        kavak_service = KavakInfoService()
        similar_records = kavak_service.search_similar(
            query=search_data.query,
            limit=search_data.limit or 5
        )
        
        return [_convert_db_to_response(record) for record in similar_records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{info_id}", response_model=KavakInfoResponse)
async def get_kavak_info(info_id: str) -> KavakInfoResponse:
    """Get a specific Kavak information record."""
    try:
        # Note: You'll need to add a get_kavak_info_by_id method to KavakInfoService
        # For now, this is a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{info_id}")
async def delete_kavak_info(info_id: str) -> Dict[str, str]:
    """Delete a Kavak information record."""
    try:
        # Note: You'll need to add a delete_kavak_info method to KavakInfoService
        # For now, this is a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 