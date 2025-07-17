#!/usr/bin/env python3
"""
Main manager for chat session initialization and management.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from db.config import Config
from services import UserService, SessionService


class ChatService:
    """Main service for chat session initialization and management."""

    def __init__(self):
        self.user_service = UserService()
        self.session_service = SessionService()

    def initialize_chat(self, phone_number: str = "1111", agent_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Initialize or get existing chat session for a user."""
        try:
            print(f"🔍 Initializing chat for phone: {phone_number}")

            # Get or create user
            user = self.user_service.get_or_create_user(phone_number)
            print(f"👤 User: {user.phone_number} (ID: {user.id})")

            # Get or create session
            session = self.session_service.get_or_create_session(user.id, agent_id)
            print(f"💬 Session: {session.id} (Started: {session.started_at})")

            # Determine session type
            session_type = "existing" if session.ended_at is None else "new"

            return {
                "user": user,
                "session": session,
                "session_type": session_type,
                "phone_number": phone_number
            }

        except Exception as e:
            print(f"❌ Error initializing chat: {e}")
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
            print(f"❌ Error getting user session: {e}")
            raise

def main():
    """Test the chat session manager."""
    print("🧪 Testing Chat Session Manager")
    print("=" * 50)

    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated")

        # Initialize chat manager
        chat_manager = ChatService()

        # Test first initialization (should create user and session)
        print("\n🔄 First initialization (should create new user and session)...")
        result1 = chat_manager.initialize_chat("1111")

        print(f"\n📊 First Run Results:")
        print(f"  - User ID: {result1['user'].id}")
        print(f"  - Phone: {result1['user'].phone_number}")
        print(f"  - Session ID: {result1['session'].id}")
        print(f"  - Session Type: {result1['session_type']}")

        # Test second initialization (should find existing user and session)
        print("\n🔄 Second initialization (should find existing user and session)...")
        result2 = chat_manager.initialize_chat("1111")

        print(f"\n📊 Second Run Results:")
        print(f"  - User ID: {result2['user'].id}")
        print(f"  - Phone: {result2['user'].phone_number}")
        print(f"  - Session ID: {result2['session'].id}")
        print(f"  - Session Type: {result2['session_type']}")

        # Verify same user and session
        if result1['user'].id == result2['user'].id:
            print("✅ Same user maintained")
        else:
            print("❌ Different users created")

        if result1['session'].id == result2['session'].id:
            print("✅ Same session maintained")
        else:
            print("❌ Different sessions created")

        print("\n🎉 Chat session manager test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()