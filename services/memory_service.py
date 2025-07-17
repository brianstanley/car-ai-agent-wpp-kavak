#!/usr/bin/env python3
"""
Memory Management Service
Handles storing and retrieving conversation messages.
"""

from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, case
from sqlalchemy.exc import SQLAlchemyError

from models.db.conversation_memory import ConversationMemoryDB
from models.db.summary import SummaryDB
from db.session import SessionLocal

class MemoryService:
    """Memory management service using SQLAlchemy."""

    def _message_to_dict(self, db_message: ConversationMemoryDB) -> Dict[str, Any]:
        """Convert database message to dictionary."""
        return {
            'id': str(db_message.id),
            'role': db_message.role,
            'content': db_message.content,
            'created_at': db_message.created_at
        }

    def _summary_to_dict(self, db_summary: SummaryDB) -> Dict[str, Any]:
        """Convert database summary to dictionary."""
        return {
            'id': str(db_summary.id),
            'text': db_summary.text,
            'created_at': db_summary.created_at
        }

    def store_message(self, chat_session_id: UUID, role: str, content: str) -> Optional[UUID]:
        """
        Store a message in the conversations_memory table.

        Args:
            chat_session_id: The ID of the chat session
            role: The role of the message sender ('user', 'assistant', 'system')
            content: The message content

        Returns:
            The ID of the stored message, or None if failed
        """
        if role not in ['user', 'assistant', 'system']:
            print(f"❌ Invalid role: {role}. Must be 'user', 'assistant', or 'system'")
            return None

        try:
            with SessionLocal() as session:
                new_message = ConversationMemoryDB(
                    chat_session_id=chat_session_id,
                    role=role,
                    content=content,
                    created_at=datetime.now(UTC)
                )
                session.add(new_message)
                session.commit()
                session.refresh(new_message)

                print(f"✅ Stored {role} message with ID: {new_message.id}")
                return new_message.id

        except SQLAlchemyError as e:
            print(f"❌ Database error storing message: {e}")
            return None

    def get_session_messages(self, chat_session_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a specific chat session.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            List of message dictionaries
        """
        try:
            with SessionLocal() as session:
                db_messages = session.scalars(
                    select(ConversationMemoryDB)
                    .where(ConversationMemoryDB.chat_session_id == chat_session_id)
                    .order_by(ConversationMemoryDB.created_at.asc())
                ).all()

                return [self._message_to_dict(msg) for msg in db_messages]

        except SQLAlchemyError as e:
            print(f"❌ Database error retrieving messages: {e}")
            return []

    def get_session_stats(self, chat_session_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a chat session.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            Dictionary with session statistics
        """
        try:
            with SessionLocal() as session:
                result = session.execute(
                    select(
                        func.count().label('total_messages'),
                        func.count(case((ConversationMemoryDB.role == 'user', 1))).label('user_messages'),
                        func.count(case((ConversationMemoryDB.role == 'assistant', 1))).label('assistant_messages'),
                        func.count(case((ConversationMemoryDB.role == 'system', 1))).label('system_messages'),
                        func.min(ConversationMemoryDB.created_at).label('first_message'),
                        func.max(ConversationMemoryDB.created_at).label('last_message')
                    )
                    .where(ConversationMemoryDB.chat_session_id == chat_session_id)
                ).first()

                if result:
                    return {
                        'total_messages': result.total_messages,
                        'user_messages': result.user_messages,
                        'assistant_messages': result.assistant_messages,
                        'system_messages': result.system_messages,
                        'first_message': result.first_message,
                        'last_message': result.last_message
                    }
                else:
                    return {}

        except SQLAlchemyError as e:
            print(f"❌ Database error getting session stats: {e}")
            return {}

    def get_last_n_messages(self, chat_session_id: UUID, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the last N messages for a chat session.

        Args:
            chat_session_id: The ID of the chat session
            n: Number of messages to retrieve (default: 10)

        Returns:
            List of message dictionaries ordered by creation time (oldest first)
        """
        try:
            with SessionLocal() as session:
                db_messages = session.scalars(
                    select(ConversationMemoryDB)
                    .where(ConversationMemoryDB.chat_session_id == chat_session_id)
                    .order_by(ConversationMemoryDB.created_at.desc())
                    .limit(n)
                ).all()

                # Convert to list and reverse to get chronological order (oldest first)
                messages_list = list(db_messages)
                messages_list.reverse()

                return [self._message_to_dict(msg) for msg in messages_list]

        except SQLAlchemyError as e:
            print(f"❌ Database error retrieving last {n} messages: {e}")
            return []

    def get_last_n_summaries(self, chat_session_id: UUID, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get the last N summaries for a chat session.

        Args:
            chat_session_id: The ID of the chat session.
            n: Number of summaries to retrieve.

        Returns:
            List of dictionaries with the summaries.
        """
        try:
            with SessionLocal() as session:
                db_summaries = session.scalars(
                    select(SummaryDB)
                    .where(SummaryDB.chat_session_id == chat_session_id)
                    .order_by(SummaryDB.created_at.desc())
                    .limit(n)
                ).all()

                return [self._summary_to_dict(summary) for summary in db_summaries]

        except SQLAlchemyError as e:
            print(f"❌ Error retrieving summaries: {e}")
            return []