#!/usr/bin/env python3
"""
Session management service.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from kavak_chatbot.models.schemas.chat_session import ChatSession
from kavak_chatbot.models.db.chat_session import ChatSessionDB
from db.session import SessionLocal

class SessionService:
    def _to_schema(self, db_session: ChatSessionDB) -> ChatSession:
        return ChatSession(
            id=db_session.id,
            user_id=db_session.user_id,
            agent_id=db_session.agent_id,
            started_at=db_session.started_at,
            ended_at=db_session.ended_at
        )

    def get_or_create_session(self, user_id: UUID, agent_id: Optional[UUID] = None) -> ChatSession:
        """Get existing active session or create new one for a user."""
        try:
            with SessionLocal() as session:
                # Check for existing active session
                db_session = session.scalar(
                    select(ChatSessionDB)
                    .where(ChatSessionDB.user_id == user_id)
                    .where(ChatSessionDB.ended_at.is_(None))
                    .order_by(ChatSessionDB.started_at.desc())
                    .limit(1)
                )

                if db_session:
                    print(f"DEBUG: Found existing active session: {db_session.id}")
                    return self._to_schema(db_session)
                else:
                    # Create new session
                    new_session = ChatSessionDB(
                        user_id=user_id,
                        agent_id=agent_id,
                        started_at=datetime.now()
                    )
                    session.add(new_session)
                    session.commit()
                    session.refresh(new_session)
                    print(f"DEBGU: Created new chat session: {new_session.id}")
                    return self._to_schema(new_session)

        except SQLAlchemyError as e:
            print(f"❌ Error in get_or_create_session: {e}")
            raise

    def get_active_session(self, user_id: UUID) -> Optional[ChatSession]:
        """Get the most recent active session for a user."""
        try:
            with SessionLocal() as session:
                db_session = session.scalar(
                    select(ChatSessionDB)
                    .where(ChatSessionDB.user_id == user_id)
                    .where(ChatSessionDB.ended_at.is_(None))
                    .order_by(ChatSessionDB.started_at.desc())
                    .limit(1)
                )

                return self._to_schema(db_session) if db_session else None

        except SQLAlchemyError as e:
            print(f"❌ Error in get_active_session: {e}")
            raise

    def create_session(self, user_id: UUID, agent_id: Optional[UUID] = None) -> ChatSession:
        """Create a new chat session for a user."""
        try:
            with SessionLocal() as session:
                new_session = ChatSessionDB(
                    user_id=user_id,
                    agent_id=agent_id,
                    started_at=datetime.now()
                )
                session.add(new_session)
                session.commit()
                session.refresh(new_session)
                print(f"🆕 Created new chat session: {new_session.id}")
                return self._to_schema(new_session)

        except SQLAlchemyError as e:
            print(f"❌ Error in create_session: {e}")
            raise

    def end_session(self, session_id: UUID) -> bool:
        """End a chat session."""
        try:
            with SessionLocal() as session:
                db_session = session.get(ChatSessionDB, session_id)
                if db_session:
                    db_session.ended_at = datetime.now()
                    session.commit()
                    print(f"✅ Session {session_id} ended successfully")
                    return True
                else:
                    print(f"❌ Session {session_id} not found")
                    return False

        except SQLAlchemyError as e:
            print(f"❌ Error in end_session: {e}")
            raise

    def get_session_by_id(self, session_id: UUID) -> Optional[ChatSession]:
        """Get session by ID."""
        try:
            with SessionLocal() as session:
                db_session = session.get(ChatSessionDB, session_id)
                return self._to_schema(db_session) if db_session else None

        except SQLAlchemyError as e:
            print(f"❌ Error in get_session_by_id: {e}")
            raise

    def get_user_sessions(self, user_id: UUID, include_ended: bool = True) -> list[ChatSession]:
        """Get all sessions for a user."""
        try:
            with SessionLocal() as session:
                query = select(ChatSessionDB).where(ChatSessionDB.user_id == user_id)

                if not include_ended:
                    query = query.where(ChatSessionDB.ended_at.is_(None))

                query = query.order_by(ChatSessionDB.started_at.desc())

                db_sessions = session.scalars(query).all()
                return [self._to_schema(session) for session in db_sessions]

        except SQLAlchemyError as e:
            print(f"❌ Error in get_user_sessions: {e}")
            raise