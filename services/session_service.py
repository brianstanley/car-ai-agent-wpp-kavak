#!/usr/bin/env python3
"""
Session management service.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from uuid import UUID
from datetime import datetime

from models.schemas.chat_session import ChatSession
from db.config import Config

class SessionService:
    """Manager for chat session operations."""

    def __init__(self):
        self.connection_string = Config.DATABASE_URL

    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)

    def get_or_create_session(self, user_id: UUID, agent_id: Optional[UUID] = None) -> ChatSession:
        """Get existing active session or create new one for a user."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check for existing active session
                    cursor.execute("""
                        SELECT id, user_id, agent_id, started_at, ended_at 
                        FROM chat_sessions 
                        WHERE user_id = %s AND ended_at IS NULL 
                        ORDER BY started_at DESC 
                        LIMIT 1
                    """, (str(user_id),))

                    session_data = cursor.fetchone()

                    if session_data:
                        print(f"✅ Found existing active session: {session_data['id']}")
                        return ChatSession(
                            id=session_data['id'],
                            user_id=session_data['user_id'],
                            agent_id=session_data['agent_id'],
                            started_at=session_data['started_at'],
                            ended_at=session_data['ended_at']
                        )
                    else:
                        # Create new session
                        cursor.execute("""
                            INSERT INTO chat_sessions (user_id, agent_id, started_at) 
                            VALUES (%s, %s, %s) 
                            RETURNING id, user_id, agent_id, started_at, ended_at
                        """, (str(user_id), str(agent_id) if agent_id else None, datetime.now()))

                        new_session_data = cursor.fetchone()
                        conn.commit()
                        print(f"🆕 Created new chat session: {new_session_data['id']}")
                        return ChatSession(
                            id=new_session_data['id'],
                            user_id=new_session_data['user_id'],
                            agent_id=new_session_data['agent_id'],
                            started_at=new_session_data['started_at'],
                            ended_at=new_session_data['ended_at']
                        )

        except Exception as e:
            print(f"❌ Error in get_or_create_session: {e}")
            raise

    def get_active_session(self, user_id: UUID) -> Optional[ChatSession]:
        """Get the most recent active session for a user."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, user_id, agent_id, started_at, ended_at 
                        FROM chat_sessions 
                        WHERE user_id = %s AND ended_at IS NULL 
                        ORDER BY started_at DESC 
                        LIMIT 1
                    """, (str(user_id),))

                    session_data = cursor.fetchone()
                    if session_data:
                        return ChatSession(
                            id=session_data['id'],
                            user_id=session_data['user_id'],
                            agent_id=session_data['agent_id'],
                            started_at=session_data['started_at'],
                            ended_at=session_data['ended_at']
                        )
                    return None

        except Exception as e:
            print(f"❌ Error in get_active_session: {e}")
            raise

    def create_session(self, user_id: UUID, agent_id: Optional[UUID] = None) -> ChatSession:
        """Create a new chat session for a user."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO chat_sessions (user_id, agent_id, started_at) 
                        VALUES (%s, %s, %s) 
                        RETURNING id, user_id, agent_id, started_at, ended_at
                    """, (str(user_id), str(agent_id) if agent_id else None, datetime.now()))

                    session_data = cursor.fetchone()
                    conn.commit()
                    print(f"🆕 Created new chat session: {session_data['id']}")
                    return ChatSession(
                        id=session_data['id'],
                        user_id=session_data['user_id'],
                        agent_id=session_data['agent_id'],
                        started_at=session_data['started_at'],
                        ended_at=session_data['ended_at']
                    )

        except Exception as e:
            print(f"❌ Error in create_session: {e}")
            raise

    def end_session(self, session_id: UUID) -> bool:
        """End a chat session."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE chat_sessions 
                        SET ended_at = %s 
                        WHERE id = %s
                    """, (datetime.now(), str(session_id)))

                    conn.commit()
                    affected_rows = cursor.rowcount
                    if affected_rows > 0:
                        print(f"✅ Session {session_id} ended successfully")
                        return True
                    else:
                        print(f"❌ Session {session_id} not found or already ended")
                        return False

        except Exception as e:
            print(f"❌ Error in end_session: {e}")
            raise

    def get_session_by_id(self, session_id: UUID) -> Optional[ChatSession]:
        """Get session by ID."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, user_id, agent_id, started_at, ended_at 
                        FROM chat_sessions 
                        WHERE id = %s
                    """, (str(session_id),))

                    session_data = cursor.fetchone()
                    if session_data:
                        return ChatSession(
                            id=session_data['id'],
                            user_id=session_data['user_id'],
                            agent_id=session_data['agent_id'],
                            started_at=session_data['started_at'],
                            ended_at=session_data['ended_at']
                        )
                    return None

        except Exception as e:
            print(f"❌ Error in get_session_by_id: {e}")
            raise