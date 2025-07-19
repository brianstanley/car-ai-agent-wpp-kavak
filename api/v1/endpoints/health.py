"""
Health check endpoints.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "Kavak WhatsApp Bot",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for Kubernetes."""
    return {
        "status": "ready",
        "service": "Kavak WhatsApp Bot"
    }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check endpoint for Kubernetes."""
    return {
        "status": "alive",
        "service": "Kavak WhatsApp Bot"
    } 