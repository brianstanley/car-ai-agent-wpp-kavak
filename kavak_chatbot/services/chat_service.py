"""
Main manager for chat session initialization and management.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from kavak_chatbot.services.user_service import UserService
from kavak_chatbot.services.session_service import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """Main service for chat session initialization and management."""

    def __init__(self):
        self.user_service = UserService()
        self.session_service = SessionService()

    def initialize_chat(self, phone_number: str = "1111", agent_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Initialize or get existing chat session for a user."""
        try:
            logger.info(f"Initializing chat for phone: {phone_number}")

            # Get or create user
            user = self.user_service.get_or_create_user(phone_number)
            logger.info(f"User: {user.phone_number} (ID: {user.id})")

            # Get or create session
            session = self.session_service.get_or_create_session(user.id, agent_id)
            logger.info(f"Session: {session.id} (Started: {session.started_at})")

            # Determine session type
            session_type = "existing" if session.ended_at is None else "new"

            return {
                "user": user,
                "session": session,
                "session_type": session_type,
                "phone_number": phone_number
            }

        except Exception as e:
            logger.error(f"Error initializing chat: {e}")
            raise

    def end_chat_session(self, session_id: UUID) -> bool:
        """End a specific chat session."""
        return self.session_service.end_session(session_id)

    def get_user_session(self, phone_number: str = "1111") -> Optional[Dict[str, Any]]:
        """Get user and their active session if exists."""
        try:
            user = self.user_service.get_user_by_phone(phone_number)
            if not user:
                return None

            session = self.session_service.get_active_session(user.id)
            if not session:
                return None

            return {
                "user": user,
                "session": session
            }

        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            raise