#!/usr/bin/env python3
"""
Memory Management Service
Handles storing and retrieving conversation messages.
"""

import os
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, case
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
from enum import Enum

from models.db.conversation_memory import ConversationMemoryDB
from models.db.summary import SummaryDB
from db.session import SessionLocal
from prompts.prompt_manager import prompt_manager

# Configuration constants
class MemorySummaryConfig:
    """Configuration constants for memory summarization."""
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_MAX_TOKENS = 300
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_WINDOW_SIZE = 10  # Number of messages to summarize
    DEFAULT_TOLERANCE = 4     # Tolerance before triggering summarization
    SUMMARY_LENGTH_WORDS = 100

class MemoryServiceError(str, Enum):
    INVALID_ROLE = "Invalid role: {role}. Must be 'user', 'assistant', or 'system'"
    DB_STORE_MESSAGE = "Database error storing message: {error}"
    DB_RETRIEVE_MESSAGES = "Database error retrieving messages: {error}"
    ERROR_RETRIEVE_WITH_SUMMARY = "Error retrieving messages with summary: {error}"
    DB_SESSION_STATS = "Database error getting session stats: {error}"
    DB_LAST_N_MESSAGES = "Database error retrieving last {n} {filter_type} messages: {error}"
    DB_RETRIEVE_SUMMARIES = "Error retrieving summaries: {error}"
    DB_UNSUMMARIZED = "Database error retrieving unsummarized messages: {error}"
    DB_GET_CREATE_SUMMARY = "Database error getting/creating summary: {error}"
    DB_MARK_SUMMARIZED = "Database error marking messages as summarized: {error}"
    OPENAI_KEY_MISSING = "OPENAI_API_KEY not found in environment variables"
    ERROR_GENERATE_SUMMARY = "Error generating summary: {error}"
    ERROR_SHOULD_SUMMARIZE = "Error checking if should summarize: {error}"
    ERROR_SUMMARIZE_CONV = "Error summarizing conversation: {error}"
    DB_UPDATE_SUMMARY = "Database error updating summary: {error}"
    DB_GET_SUMMARY = "Database error getting summary: {error}"

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
            print(MemoryServiceError.INVALID_ROLE.value.format(role=role))
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
            print(MemoryServiceError.DB_STORE_MESSAGE.value.format(error=e))
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
            print(MemoryServiceError.DB_RETRIEVE_MESSAGES.value.format(error=e))
            return []



    def get_session_messages_with_summary(self, chat_session_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a specific chat session with summary included.
        This includes unsummarized messages plus the conversation summary.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            List of message dictionaries with summary included
        """
        try:
            messages = []

            # Get conversation summary
            summary = self.get_conversation_summary(chat_session_id)
            if summary and summary.get('text'):
                # Add summary as a system message at the beginning
                summary_message = {
                    'id': f"summary_{summary['id']}",
                    'role': 'system',
                    'content': f"RESUMEN DE CONVERSACIÓN PASADA:\n{summary['text']}",
                    'created_at': summary.get('created_at')
                }
                messages.append(summary_message)

            # Get unsummarized messages (last 10 by default)
            unsummarized_messages = self.get_last_n_messages(chat_session_id, n=10, unsummarized_only=True)
            messages.extend(unsummarized_messages)

            return messages

        except Exception as e:
            print(MemoryServiceError.ERROR_RETRIEVE_WITH_SUMMARY.value.format(error=e))
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
            print(MemoryServiceError.DB_SESSION_STATS.value.format(error=e))
            return {}

    def get_last_n_messages(self, chat_session_id: UUID, n: int = 10, unsummarized_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the last N messages for a chat session.

        Args:
            chat_session_id: The ID of the chat session
            n: Number of messages to retrieve (default: 10)
            unsummarized_only: If True, only return unsummarized messages (default: False)

        Returns:
            List of message dictionaries ordered by creation time (oldest first)
        """
        try:
            with SessionLocal() as session:
                query = select(ConversationMemoryDB).where(
                    ConversationMemoryDB.chat_session_id == chat_session_id
                )
                
                # Add filter for unsummarized messages if requested
                if unsummarized_only:
                    query = query.where(ConversationMemoryDB.summarized == False)
                
                db_messages = session.scalars(
                    query.order_by(ConversationMemoryDB.created_at.desc()).limit(n)
                ).all()

                # Convert to list and reverse to get chronological order (oldest first)
                messages_list = list(db_messages)
                messages_list.reverse()

                return [self._message_to_dict(msg) for msg in messages_list]

        except SQLAlchemyError as e:
            filter_type = "unsummarized" if unsummarized_only else "all"
            print(MemoryServiceError.DB_LAST_N_MESSAGES.value.format(n=n, filter_type=filter_type, error=e))
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
            print(MemoryServiceError.DB_RETRIEVE_SUMMARIES.value.format(error=e))
            return []

    def _get_unsummarized_messages(self, chat_session_id: UUID, limit: Optional[int] = None) -> List[ConversationMemoryDB]:
        """
        Get unsummarized messages for a chat session.

        Args:
            chat_session_id: The ID of the chat session
            limit: Maximum number of messages to retrieve

        Returns:
            List of unsummarized messages ordered by creation time (oldest first)
        """
        try:
            with SessionLocal() as session:
                query = (
                    select(ConversationMemoryDB)
                    .where(
                        ConversationMemoryDB.chat_session_id == chat_session_id,
                        ConversationMemoryDB.summarized == False
                    )
                    .order_by(ConversationMemoryDB.created_at.asc())
                )

                if limit:
                    query = query.limit(limit)

                return list(session.scalars(query).all())

        except SQLAlchemyError as e:
            print(MemoryServiceError.DB_UNSUMMARIZED.value.format(error=e))
            return []

    def _get_or_create_summary(self, chat_session_id: UUID) -> Optional[SummaryDB]:
        """
        Get existing summary or create a new one for a chat session.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            SummaryDB object or None if failed
        """
        try:
            with SessionLocal() as session:
                # Try to get existing summary
                existing_summary = session.scalar(
                    select(SummaryDB)
                    .where(SummaryDB.chat_session_id == chat_session_id)
                    .order_by(SummaryDB.created_at.desc())
                )

                if existing_summary:
                    return existing_summary
                else:
                    # Create new summary
                    new_summary = SummaryDB(
                        chat_session_id=chat_session_id,
                        text="",
                        message_count=0
                    )
                    session.add(new_summary)
                    session.commit()
                    session.refresh(new_summary)
                    return new_summary

        except SQLAlchemyError as e:
            print(MemoryServiceError.DB_GET_CREATE_SUMMARY.value.format(error=e))
            return None

    def _mark_messages_as_summarized(self, message_ids: List[UUID]) -> bool:
        """
        Mark messages as summarized.

        Args:
            message_ids: List of message IDs to mark as summarized

        Returns:
            True if successful, False otherwise
        """
        try:
            with SessionLocal() as session:
                # Get messages and mark them as summarized
                messages = session.scalars(
                    select(ConversationMemoryDB)
                    .where(ConversationMemoryDB.id.in_(message_ids))
                ).all()

                for message in messages:
                    message.summarized = True

                session.commit()
                return True

        except SQLAlchemyError as e:
            print(MemoryServiceError.DB_MARK_SUMMARIZED.value.format(error=e))
            return False

    def _generate_summary(self, messages: List[ConversationMemoryDB], old_summary: Optional[str] = None) -> str:
        """
        Generate summary using OpenAI API.

        Args:
            messages: List of messages to summarize
            old_summary: Optional previous summary to consider when generating new summary

        Returns:
            Generated summary text
        """
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(MemoryServiceError.OPENAI_KEY_MISSING.value)
                return "Error: OpenAI API key not configured"

            client = OpenAI(api_key=api_key)

            # Format messages for summarization
            conversation_text = self._format_messages_for_summary(messages)

            # Get prompt from prompts folder
            prompt = prompt_manager.get_conversation_summary_prompt(
                old_summary=old_summary or "[NINGUNO]",
                conversation_text=conversation_text,
                summary_length_words=MemorySummaryConfig.SUMMARY_LENGTH_WORDS
            )
            
            # Get system prompt from prompts folder
            system_prompt = prompt_manager.get_conversation_summary_system_prompt()
            
            # Generate summary
            response = client.chat.completions.create(
                model=MemorySummaryConfig.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MemorySummaryConfig.DEFAULT_MAX_TOKENS,
                temperature=MemorySummaryConfig.DEFAULT_TEMPERATURE
            )

            summary = response.choices[0].message.content
            return summary.strip() if summary else "No se pudo generar resumen"

        except Exception as e:
            print(MemoryServiceError.ERROR_GENERATE_SUMMARY.value.format(error=e))
            return f"Error generando resumen: {e}"

    def _format_messages_for_summary(self, messages: List[ConversationMemoryDB]) -> str:
        """
        Format messages for summarization prompt.

        Args:
            messages: List of messages to format

        Returns:
            Formatted conversation text
        """
        formatted_lines = []

        for i, msg in enumerate(messages, 1):
            role = "Usuario" if msg.role == 'user' else "Agente"
            content = msg.content.strip()

            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "..."

            formatted_lines.append(f"{i}. {role}: {content}")

        return "\n\n".join(formatted_lines)

    def should_summarize_conversation(self, chat_session_id: UUID) -> bool:
        """
        Check if conversation should be summarized based on sliding window.
        Triggers when there are N + tolerance unsummarized messages accumulated.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            True if should summarize, False otherwise
        """
        try:
            # Get ALL unsummarized messages (without limit)
            unsummarized_messages = self._get_unsummarized_messages(chat_session_id)

            # Check if we have enough accumulated unsummarized messages to trigger
            trigger_threshold = MemorySummaryConfig.DEFAULT_WINDOW_SIZE + MemorySummaryConfig.DEFAULT_TOLERANCE

            print(f"   Unsummarized messages: {len(unsummarized_messages)} (need {trigger_threshold} to trigger)")

            return len(unsummarized_messages) >= trigger_threshold

        except Exception as e:
            print(MemoryServiceError.ERROR_SHOULD_SUMMARIZE.value.format(error=e))
            return False

    def summarize_conversation(self, chat_session_id: UUID) -> bool:
        """
        Summarize conversation using sliding window strategy.
        When N + tolerance messages are accumulated, summarize only the first N messages.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            True if summarization was successful, False otherwise
        """
        try:
            print(f"Summarizing conversation for session: {chat_session_id}")

            # Get ALL unsummarized messages (without limit)
            all_unsummarized_messages = self._get_unsummarized_messages(chat_session_id)

            if not all_unsummarized_messages:
                print("   No unsummarized messages found")
                return True

            trigger_threshold = MemorySummaryConfig.DEFAULT_WINDOW_SIZE + MemorySummaryConfig.DEFAULT_TOLERANCE
            print(f"   Found {len(all_unsummarized_messages)} total unsummarized messages (need {trigger_threshold} to trigger)")

            # Only summarize if we have enough accumulated messages to trigger
            if len(all_unsummarized_messages) < trigger_threshold:
                print(f"   Not enough accumulated messages to summarize. Need {trigger_threshold}, have {len(all_unsummarized_messages)}")
                return True

            # Take only the first N messages (oldest ones) for summarization
            messages_to_summarize = all_unsummarized_messages[:MemorySummaryConfig.DEFAULT_WINDOW_SIZE]
            print(f"   Will summarize {len(messages_to_summarize)} messages (first {MemorySummaryConfig.DEFAULT_WINDOW_SIZE} of {len(all_unsummarized_messages)} accumulated)")

            # Get existing summary to pass to the generation method
            existing_summary = self.get_conversation_summary(chat_session_id)
            old_summary_text = existing_summary.get('text') if existing_summary else None

            if old_summary_text:
                print(f"   Found existing summary, will consider it when generating new summary")

            # Generate summary
            summary_text = self._generate_summary(messages_to_summarize, old_summary_text)

            # Get or create summary record
            summary_record = self._get_or_create_summary(chat_session_id)
            if not summary_record:
                print("   Failed to get/create summary record")
                return False

            # Update summary
            try:
                with SessionLocal() as session:
                    summary_record.text = summary_text
                    summary_record.message_count = len(messages_to_summarize)
                    summary_record.last_message_id = messages_to_summarize[-1].id
                    summary_record.period_start = messages_to_summarize[0].created_at
                    summary_record.period_end = messages_to_summarize[-1].created_at
                    summary_record.updated_at = datetime.now(UTC)

                    session.add(summary_record)
                    session.commit()

                    print(f"   Summary updated successfully")

                    # Mark messages as summarized (only the ones we actually summarized)
                    message_ids = [str(msg.id) for msg in messages_to_summarize]
                    if self._mark_messages_as_summarized([UUID(msg_id) for msg_id in message_ids]):
                        print(f"   Marked {len(message_ids)} messages as summarized")
                        print(f"   Remaining unsummarized: {len(all_unsummarized_messages) - len(messages_to_summarize)} messages")
                        return True
                    else:
                        print("   Failed to mark messages as summarized")
                        return False

            except SQLAlchemyError as e:
                print(MemoryServiceError.DB_UPDATE_SUMMARY.value.format(error=e))
                return False

        except Exception as e:
            print(MemoryServiceError.ERROR_SUMMARIZE_CONV.value.format(error=e))
            return False

    def get_conversation_summary(self, chat_session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the current summary for a chat session.

        Args:
            chat_session_id: The ID of the chat session

        Returns:
            Summary dictionary or None if not found
        """
        try:
            with SessionLocal() as session:
                summary = session.scalar(
                    select(SummaryDB)
                    .where(SummaryDB.chat_session_id == chat_session_id)
                    .order_by(SummaryDB.created_at.desc())
                )

                if summary:
                    return {
                        'id': str(summary.id),
                        'text': summary.text,
                        'message_count': summary.message_count,
                        'period_start': summary.period_start,
                        'period_end': summary.period_end,
                        'created_at': summary.created_at,
                        'updated_at': summary.updated_at
                    }
                else:
                    return None

        except SQLAlchemyError as e:
            print(MemoryServiceError.DB_GET_SUMMARY.value.format(error=e))
            return None