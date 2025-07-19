"""
API v1 package for Kavak WhatsApp Bot.
"""

from fastapi import APIRouter
from .endpoints import whatsapp, health, users, chat, kavak_info

# Create main v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_v1_router.include_router(whatsapp.router, tags=["WhatsApp"])
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(users.router, tags=["Users"])
api_v1_router.include_router(chat.router, tags=["Chat"])
api_v1_router.include_router(kavak_info.router, tags=["Kavak Info"]) 