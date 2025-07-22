#!/usr/bin/env python3
"""
Unit tests for MemoryService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError

from services.memory_service import MemoryService, MemorySummaryConfig
from models.db.conversation_memory import ConversationMemoryDB
from models.db.summary import SummaryDB


class TestMemoryService:
    """Test cases for MemoryService"""

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService instance for testing."""
        return MemoryService()

    @pytest.fixture
    def sample_chat_session_id(self):
        """Sample chat session ID for testing."""
        return uuid4()

    @pytest.fixture
    def sample_message_data(self):
        """Sample message data for testing."""
        return {
            'role': 'user',
            'content': 'Hello, how are you?',
            'created_at': datetime.now(UTC)
        }

    @pytest.fixture
    def sample_messages(self, sample_chat_session_id):
        """Sample conversation messages for testing."""
        return [
            ConversationMemoryDB(
                id=uuid4(),
                chat_session_id=sample_chat_session_id,
                role='user',
                content='Hello, I need help with car financing',
                created_at=datetime.now(UTC),
                summarized=False
            ),
            ConversationMemoryDB(
                id=uuid4(),
                chat_session_id=sample_chat_session_id,
                role='assistant',
                content='I can help you with car financing options. What type of car are you looking for?',
                created_at=datetime.now(UTC),
                summarized=False
            ),
            ConversationMemoryDB(
                id=uuid4(),
                chat_session_id=sample_chat_session_id,
                role='user',
                content='I want a Toyota Camry',
                created_at=datetime.now(UTC),
                summarized=False
            )
        ]

    @pytest.fixture
    def sample_summary(self, sample_chat_session_id):
        """Sample summary for testing."""
        return SummaryDB(
            id=uuid4(),
            chat_session_id=sample_chat_session_id,
            text='User inquired about car financing for a Toyota Camry',
            created_at=datetime.now(UTC)
        )

    def test_message_to_dict(self, memory_service, sample_messages):
        """Test _message_to_dict method."""
        message = sample_messages[0]
        result = memory_service._message_to_dict(message)
        
        assert result['id'] == str(message.id)
        assert result['role'] == message.role
        assert result['content'] == message.content
        assert result['created_at'] == message.created_at

    def test_summary_to_dict(self, memory_service, sample_summary):
        """Test _summary_to_dict method."""
        result = memory_service._summary_to_dict(sample_summary)
        
        assert result['id'] == str(sample_summary.id)
        assert result['text'] == sample_summary.text
        assert result['created_at'] == sample_summary.created_at

    @patch('services.memory_service.SessionLocal')
    def test_store_message_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_message_data):
        """Test successful message storage."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock the new message
        mock_message = Mock()
        mock_message.id = uuid4()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Mock the ConversationMemoryDB constructor to return our mock
        with patch('services.memory_service.ConversationMemoryDB') as mock_conversation_memory:
            mock_conversation_memory.return_value = mock_message
            
            result = memory_service.store_message(
                sample_chat_session_id,
                sample_message_data['role'],
                sample_message_data['content']
            )
            
            assert result == mock_message.id
            mock_session.add.assert_called_once_with(mock_message)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_message)

    @patch('services.memory_service.SessionLocal')
    def test_store_message_invalid_role(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test message storage with invalid role."""
        result = memory_service.store_message(sample_chat_session_id, 'invalid_role', 'test content')
        
        assert result is None

    @patch('services.memory_service.SessionLocal')
    def test_store_message_database_error(self, mock_session_local, memory_service, sample_chat_session_id, sample_message_data):
        """Test message storage with database error."""
        # Mock session to raise exception
        mock_session = Mock()
        mock_session.add.side_effect = SQLAlchemyError("Database error")
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock the ConversationMemoryDB constructor
        with patch('services.memory_service.ConversationMemoryDB') as mock_conversation_memory:
            mock_conversation_memory.return_value = Mock()
            
            result = memory_service.store_message(
                sample_chat_session_id,
                sample_message_data['role'],
                sample_message_data['content']
            )
            
            assert result is None

    @patch('services.memory_service.SessionLocal')
    def test_get_session_messages_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_messages):
        """Test successful retrieval of session messages."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_session.scalars.return_value.all.return_value = sample_messages
        
        result = memory_service.get_session_messages(sample_chat_session_id)
        
        assert len(result) == len(sample_messages)
        for i, message in enumerate(result):
            assert message['id'] == str(sample_messages[i].id)
            assert message['role'] == sample_messages[i].role
            assert message['content'] == sample_messages[i].content

    @patch('services.memory_service.SessionLocal')
    def test_get_session_messages_database_error(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test message retrieval with database error."""
        # Mock session to raise exception
        mock_session = Mock()
        mock_session.scalars.side_effect = SQLAlchemyError("Database error")
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        result = memory_service.get_session_messages(sample_chat_session_id)
        
        assert result == []

    @patch('services.memory_service.SessionLocal')
    def test_get_session_stats_success(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test successful retrieval of session statistics."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.total_messages = 10
        mock_result.user_messages = 5
        mock_result.assistant_messages = 4
        mock_result.system_messages = 1
        mock_result.first_message = datetime.now(UTC)
        mock_result.last_message = datetime.now(UTC)
        
        mock_session.execute.return_value.first.return_value = mock_result
        
        result = memory_service.get_session_stats(sample_chat_session_id)
        
        assert result['total_messages'] == 10
        assert result['user_messages'] == 5
        assert result['assistant_messages'] == 4
        assert result['system_messages'] == 1
        assert 'first_message' in result
        assert 'last_message' in result

    @patch('services.memory_service.SessionLocal')
    def test_get_session_stats_no_data(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test session statistics when no data exists."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result with no data
        mock_session.execute.return_value.first.return_value = None
        
        result = memory_service.get_session_stats(sample_chat_session_id)
        
        assert result == {}

    @patch('services.memory_service.SessionLocal')
    def test_get_last_n_messages_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_messages):
        """Test successful retrieval of last N messages."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result - return messages in reverse order (as they would be from DESC query)
        reversed_messages = list(reversed(sample_messages))
        mock_session.scalars.return_value.all.return_value = reversed_messages
        
        result = memory_service.get_last_n_messages(sample_chat_session_id, n=2)
        
        assert len(result) == len(sample_messages)
        # Should be in chronological order (oldest first) after reversing
        assert result[0]['id'] == str(sample_messages[0].id)

    @patch('services.memory_service.SessionLocal')
    def test_get_last_n_messages_unsummarized_only(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test retrieval of last N unsummarized messages."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_session.scalars.return_value.all.return_value = []
        
        result = memory_service.get_last_n_messages(sample_chat_session_id, n=5, unsummarized_only=True)
        
        assert result == []

    @patch('services.memory_service.SessionLocal')
    def test_get_last_n_summaries_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_summary):
        """Test successful retrieval of last N summaries."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_session.scalars.return_value.all.return_value = [sample_summary]
        
        result = memory_service.get_last_n_summaries(sample_chat_session_id, n=3)
        
        assert len(result) == 1
        assert result[0]['id'] == str(sample_summary.id)
        assert result[0]['text'] == sample_summary.text

    @patch('services.memory_service.SessionLocal')
    def test_get_last_n_summaries_database_error(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test summary retrieval with database error."""
        # Mock session to raise exception
        mock_session = Mock()
        mock_session.scalars.side_effect = SQLAlchemyError("Database error")
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        result = memory_service.get_last_n_summaries(sample_chat_session_id, n=3)
        
        assert result == []

    @patch('services.memory_service.SessionLocal')
    def test_get_unsummarized_messages_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_messages):
        """Test successful retrieval of unsummarized messages."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_session.scalars.return_value.all.return_value = sample_messages
        
        result = memory_service._get_unsummarized_messages(sample_chat_session_id, limit=10)
        
        assert len(result) == len(sample_messages)

    @patch('services.memory_service.SessionLocal')
    @patch('services.memory_service.select')
    def test_get_or_create_summary_new_summary(self, mock_select, mock_session_local, memory_service, sample_chat_session_id):
        """Test creating a new summary when none exists."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result - no existing summary
        mock_session.scalar.return_value = None
        
        # Mock the new summary
        mock_summary = Mock()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Mock the SummaryDB constructor properly
        with patch('services.memory_service.SummaryDB') as mock_summary_db:
            mock_summary_db.return_value = mock_summary
            
            result = memory_service._get_or_create_summary(sample_chat_session_id)
            
            assert result == mock_summary
            mock_session.add.assert_called_once_with(mock_summary)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_summary)

    @patch('services.memory_service.SessionLocal')
    def test_get_or_create_summary_existing_summary(self, mock_session_local, memory_service, sample_chat_session_id, sample_summary):
        """Test retrieving existing summary."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result - existing summary
        mock_session.scalar.return_value = sample_summary
        
        result = memory_service._get_or_create_summary(sample_chat_session_id)
        
        assert result == sample_summary

    @patch('services.memory_service.SessionLocal')
    def test_mark_messages_as_summarized_success(self, mock_session_local, memory_service):
        """Test successful marking of messages as summarized."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock messages
        mock_message1 = Mock()
        mock_message2 = Mock()
        mock_session.scalars.return_value.all.return_value = [mock_message1, mock_message2]
        
        message_ids = [uuid4(), uuid4()]
        
        result = memory_service._mark_messages_as_summarized(message_ids)
        
        assert result is True
        mock_session.commit.assert_called_once()
        # Check that summarized was set to True for each message
        assert mock_message1.summarized is True
        assert mock_message2.summarized is True

    @patch('services.memory_service.SessionLocal')
    def test_mark_messages_as_summarized_failure(self, mock_session_local, memory_service):
        """Test failure when marking messages as summarized."""
        # Mock session to raise exception
        mock_session = Mock()
        mock_session.scalars.side_effect = SQLAlchemyError("Database error")
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        message_ids = [uuid4(), uuid4()]
        
        result = memory_service._mark_messages_as_summarized(message_ids)
        
        assert result is False

    @patch('services.memory_service.OpenAI')
    @patch('services.memory_service.prompt_manager')
    @patch('os.getenv')
    def test_generate_summary_success(self, mock_getenv, mock_prompt_manager, mock_openai, memory_service, sample_messages):
        """Test successful summary generation."""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"
        
        # Mock prompt manager
        mock_prompt_manager.get_conversation_summary_prompt.return_value = "Test prompt"
        mock_prompt_manager.get_conversation_summary_system_prompt.return_value = "Test system prompt"
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "User inquired about car financing for a Toyota Camry"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = memory_service._generate_summary(sample_messages)
        
        assert result == "User inquired about car financing for a Toyota Camry"
        mock_client.chat.completions.create.assert_called_once()

    @patch('services.memory_service.OpenAI')
    @patch('services.memory_service.prompt_manager')
    @patch('os.getenv')
    def test_generate_summary_with_old_summary(self, mock_getenv, mock_prompt_manager, mock_openai, memory_service, sample_messages):
        """Test summary generation with existing summary."""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"
        
        # Mock prompt manager
        mock_prompt_manager.get_conversation_summary_prompt.return_value = "Test prompt"
        mock_prompt_manager.get_conversation_summary_system_prompt.return_value = "Test system prompt"
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Updated summary with new information"
        mock_client.chat.completions.create.return_value = mock_response
        
        old_summary = "Previous conversation about car financing"
        result = memory_service._generate_summary(sample_messages, old_summary)
        
        assert result == "Updated summary with new information"
        mock_client.chat.completions.create.assert_called_once()

    def test_format_messages_for_summary(self, memory_service, sample_messages):
        """Test formatting messages for summary generation."""
        result = memory_service._format_messages_for_summary(sample_messages)
        
        assert "1. Usuario: Hello, I need help with car financing" in result
        assert "2. Agente: I can help you with car financing options" in result
        assert "3. Usuario: I want a Toyota Camry" in result

    @patch('services.memory_service.MemoryService._get_unsummarized_messages')
    def test_should_summarize_conversation_true(self, mock_get_unsummarized, memory_service, sample_chat_session_id):
        """Test that summarization should occur when conditions are met."""
        # Mock many unsummarized messages
        mock_messages = [Mock() for _ in range(18)]  # DEFAULT_WINDOW_SIZE + DEFAULT_TOLERANCE (12 + 6)
        mock_get_unsummarized.return_value = mock_messages
    
        result = memory_service.should_summarize_conversation(sample_chat_session_id)
    
        assert result is True

    @patch('services.memory_service.MemoryService._get_unsummarized_messages')
    def test_should_summarize_conversation_false(self, mock_get_unsummarized, memory_service, sample_chat_session_id):
        """Test that summarization should not occur when conditions are not met."""
        # Mock few unsummarized messages
        mock_messages = [Mock() for _ in range(5)]  # Less than DEFAULT_WINDOW_SIZE + DEFAULT_TOLERANCE
        mock_get_unsummarized.return_value = mock_messages
        
        result = memory_service.should_summarize_conversation(sample_chat_session_id)
        
        assert result is False

    @patch('services.memory_service.MemoryService.should_summarize_conversation')
    @patch('services.memory_service.MemoryService._get_unsummarized_messages')
    @patch('services.memory_service.MemoryService._get_or_create_summary')
    @patch('services.memory_service.MemoryService._generate_summary')
    @patch('services.memory_service.MemoryService._mark_messages_as_summarized')
    @patch('services.memory_service.MemoryService.get_conversation_summary')
    @patch('services.memory_service.SessionLocal')
    def test_summarize_conversation_success(self, mock_session_local, mock_get_summary, 
                                          mock_mark_summarized, mock_generate_summary, 
                                          mock_get_or_create_summary, mock_get_unsummarized, 
                                          mock_should_summarize, memory_service, sample_chat_session_id, sample_messages):
        """Test successful conversation summarization."""
        # Mock dependencies - need enough messages to trigger summarization
        mock_should_summarize.return_value = True
        # Create enough messages to meet the threshold (18 messages needed: DEFAULT_WINDOW_SIZE + DEFAULT_TOLERANCE)
        mock_messages = []
        for i in range(18):
            mock_msg = Mock()
            mock_msg.id = uuid4()
            mock_msg.created_at = datetime.now(UTC)
            mock_messages.append(mock_msg)
        mock_get_unsummarized.return_value = mock_messages
        mock_summary = Mock()
        mock_get_or_create_summary.return_value = mock_summary
        mock_generate_summary.return_value = "Test summary"
        mock_mark_summarized.return_value = True
        mock_get_summary.return_value = None  # No existing summary
        
        # Mock session for the update operation
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        result = memory_service.summarize_conversation(sample_chat_session_id)
        
        assert result is True
        mock_generate_summary.assert_called_once()
        mock_mark_summarized.assert_called_once()

    @patch('services.memory_service.MemoryService.should_summarize_conversation')
    def test_summarize_conversation_not_needed(self, mock_should_summarize, memory_service, sample_chat_session_id):
        """Test summarization when not needed."""
        mock_should_summarize.return_value = False
        
        result = memory_service.summarize_conversation(sample_chat_session_id)
        
        assert result is True  # Returns True when no summarization needed

    @patch('services.memory_service.MemoryService.get_conversation_summary')
    @patch('services.memory_service.MemoryService.get_last_n_messages')
    def test_get_session_messages_with_summary_success(self, mock_get_last_n, mock_get_summary, 
                                                     memory_service, sample_chat_session_id, sample_summary):
        """Test successful retrieval of messages with summary."""
        # Mock dependencies
        mock_get_summary.return_value = {
            'id': str(sample_summary.id),
            'text': sample_summary.text,
            'created_at': sample_summary.created_at
        }
        mock_get_last_n.return_value = [
            {'id': '1', 'role': 'user', 'content': 'test', 'created_at': datetime.now(UTC)}
        ]
        
        result = memory_service.get_session_messages_with_summary(sample_chat_session_id)
        
        assert len(result) == 2  # Summary + 1 message
        assert result[0]['role'] == 'system'
        assert 'RESUMEN DE CONVERSACIÓN PASADA:' in result[0]['content']

    @patch('services.memory_service.MemoryService.get_conversation_summary')
    def test_get_session_messages_with_summary_no_summary(self, mock_get_summary, memory_service, sample_chat_session_id):
        """Test retrieval of messages when no summary exists."""
        mock_get_summary.return_value = None
        
        result = memory_service.get_session_messages_with_summary(sample_chat_session_id)
        
        assert result == []

    @patch('services.memory_service.SessionLocal')
    def test_get_conversation_summary_success(self, mock_session_local, memory_service, sample_chat_session_id, sample_summary):
        """Test successful retrieval of conversation summary."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_session.scalar.return_value = sample_summary
        
        result = memory_service.get_conversation_summary(sample_chat_session_id)
        
        assert result['id'] == str(sample_summary.id)
        assert result['text'] == sample_summary.text
        assert result['created_at'] == sample_summary.created_at

    @patch('services.memory_service.SessionLocal')
    def test_get_conversation_summary_not_found(self, mock_session_local, memory_service, sample_chat_session_id):
        """Test retrieval of conversation summary when none exists."""
        # Mock session
        mock_session = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock query result - no summary
        mock_session.scalar.return_value = None
        
        result = memory_service.get_conversation_summary(sample_chat_session_id)
        
        assert result is None


class TestMemorySummaryConfig:
    """Test cases for MemorySummaryConfig"""

    def test_config_constants(self):
        """Test that configuration constants are properly set."""
        assert MemorySummaryConfig.DEFAULT_MODEL == "gpt-3.5-turbo"
        assert MemorySummaryConfig.DEFAULT_MAX_TOKENS == 300
        assert MemorySummaryConfig.DEFAULT_TEMPERATURE == 0.1
        assert MemorySummaryConfig.DEFAULT_WINDOW_SIZE == 12
        assert MemorySummaryConfig.DEFAULT_TOLERANCE == 6
        assert MemorySummaryConfig.SUMMARY_LENGTH_WORDS == 100 