"""
Chat session management endpoints.
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException

from kavak_chatbot.services.llm_openai_adapter import OpenAIClientAdapter
from kavak_chatbot.services.prompt_builder import PromptBuilder
from kavak_chatbot.services.session_service import SessionService
from kavak_chatbot.services import MemoryService, AgentService, UserService, ChatService
from kavak_chatbot.models.schemas.chat import (
    ChatSessionResponse,
    ChatSessionCreateRequest,
    MessageResponse,
    SessionStatsResponse,
    SummaryResponse
)
from pydantic import BaseModel
from uuid import UUID
import os
from kavak_chatbot.utils import OpenAITokenizerWrapper, truncate_text_to_max_tokens
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class SendMessageRequest(BaseModel):
    session_id: str
    message: str


class SendMessageResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    message_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(session_data: ChatSessionCreateRequest) -> ChatSessionResponse:
    try:
        from uuid import UUID
        agent_id = None
        if session_data.agent_id:
            agent_id = UUID(session_data.agent_id)
        else:
            default_agent_id = os.getenv("DEFAULT_KAVAK_AGENT_ID", "22222222-2222-2222-2222-222222222222")
            agent_id = UUID(default_agent_id)

        chat_service = ChatService()
        session_info = chat_service.initialize_chat(session_data.phone_number, agent_id)

        session = session_info.session
        return ChatSessionResponse(
            id=str(session.id),
            user_id=str(session.user_id),
            agent_id=str(session.agent_id) if session.agent_id else None,
            started_at=session.started_at.isoformat() if session.started_at else "",
            ended_at=session.ended_at.isoformat() if session.ended_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid agent ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_all_sessions(limit: int = 50, offset: int = 0, include_ended: bool = True) -> List[ChatSessionResponse]:
    try:
        session_service = SessionService()
        sessions = session_service.get_all_sessions(limit=limit, offset=offset, include_ended=include_ended)

        return [
            ChatSessionResponse(
                id=str(session.id),
                user_id=str(session.user_id),
                agent_id=str(session.agent_id) if session.agent_id else None,
                started_at=session.started_at.isoformat() if session.started_at else "",
                ended_at=session.ended_at.isoformat() if session.ended_at else None
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str) -> ChatSessionResponse:
    try:
        from uuid import UUID
        session_service = SessionService()
        session = session_service.get_session_by_id(UUID(session_id))

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return ChatSessionResponse(
            id=str(session.id),
            user_id=str(session.user_id),
            agent_id=str(session.agent_id) if session.agent_id else None,
            started_at=session.started_at.isoformat() if session.started_at else "",
            ended_at=session.ended_at.isoformat() if session.ended_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/end")
async def end_chat_session(session_id: str) -> Dict[str, str]:
    try:
        chat_service = ChatService()
        success = chat_service.end_chat_session(UUID(session_id))

        if success:
            return {"message": "Chat session ended successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/user/{phone_number}", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions(phone_number: str) -> List[ChatSessionResponse]:
    try:
        from uuid import UUID
        from kavak_chatbot.services import UserService

        user_service = UserService()
        user = user_service.get_user_by_phone(phone_number)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session_service = SessionService()
        sessions = session_service.get_user_sessions(UUID(str(user.id)))

        return [
            ChatSessionResponse(
                id=str(session.id),
                user_id=str(session.user_id),
                agent_id=str(session.agent_id) if session.agent_id else None,
                started_at=session.started_at.isoformat() if session.started_at else "",
                ended_at=session.ended_at.isoformat() if session.ended_at else None
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/user-id/{user_id}", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions_by_id(user_id: str) -> List[ChatSessionResponse]:
    try:
        from uuid import UUID
        session_service = SessionService()
        sessions = session_service.get_user_sessions(UUID(user_id))

        return [
            ChatSessionResponse(
                id=str(session.id),
                user_id=str(session.user_id),
                agent_id=str(session.agent_id) if session.agent_id else None,
                started_at=session.started_at.isoformat() if session.started_at else "",
                ended_at=session.ended_at.isoformat() if session.ended_at else None
            )
            for session in sessions
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str) -> List[MessageResponse]:
    try:
        from uuid import UUID
        memory_service = MemoryService()
        messages = memory_service.get_session_messages(UUID(session_id))

        return [
            MessageResponse(
                id=msg['id'],
                role=msg['role'],
                content=msg['content'],
                created_at=msg['created_at'].isoformat() if msg['created_at'] else ""
            )
            for msg in messages
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages/last/{limit}", response_model=List[MessageResponse])
async def get_last_session_messages(session_id: str, limit: int = 10) -> List[MessageResponse]:
    try:
        from uuid import UUID
        memory_service = MemoryService()
        messages = memory_service.get_last_n_messages(UUID(session_id), limit)

        return [
            MessageResponse(
                id=msg['id'],
                role=msg['role'],
                content=msg['content'],
                created_at=msg['created_at'].isoformat() if msg['created_at'] else ""
            )
            for msg in messages
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session_id: str) -> SessionStatsResponse:
    try:
        from uuid import UUID
        memory_service = MemoryService()
        stats = memory_service.get_session_stats(UUID(session_id))

        first_message = stats.get('first_message')
        last_message = stats.get('last_message')

        return SessionStatsResponse(
            total_messages=stats.get('total_messages', 0),
            user_messages=stats.get('user_messages', 0),
            assistant_messages=stats.get('assistant_messages', 0),
            system_messages=stats.get('system_messages', 0),
            first_message=first_message.isoformat() if first_message else None,
            last_message=last_message.isoformat() if last_message else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summaries", response_model=List[SummaryResponse])
async def get_session_summaries(session_id: str) -> List[SummaryResponse]:
    try:
        from uuid import UUID
        memory_service = MemoryService()
        summaries = memory_service.get_last_n_summaries(UUID(session_id), 10)  # Get last 10 summaries

        return [
            SummaryResponse(
                id=summary['id'],
                text=summary['text'],
                created_at=summary['created_at'].isoformat() if summary['created_at'] else ""
            )
            for summary in summaries
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message", response_model=SendMessageResponse)
async def send_message_to_agent(request: SendMessageRequest) -> SendMessageResponse:
    try:
        MAX_USER_QUERY_TOKENS = int(os.getenv("MAX_USER_QUERY_TOKENS", 1024))
        tokenizer = OpenAITokenizerWrapper(model_name="cl100k_base")
        num_tokens = len(tokenizer.tokenize(request.message))
        user_message = request.message
        if num_tokens > MAX_USER_QUERY_TOKENS:
            user_message = truncate_text_to_max_tokens(request.message, MAX_USER_QUERY_TOKENS, model_name="cl100k_base")
            logging.warning(f"User message exceeded {MAX_USER_QUERY_TOKENS} tokens and was truncated.")

        try:
            session_id = UUID(request.session_id)
        except ValueError:
            return SendMessageResponse(
                success=False,
                response="",
                session_id=request.session_id,
                error="Invalid session ID format"
            )

        session_service = SessionService()
        session = session_service.get_session_by_id(session_id)

        if not session:
            return SendMessageResponse(
                success=False,
                response="",
                session_id=request.session_id,
                error="Session not found"
            )

        user_service = UserService()
        user = user_service.get_user_by_id(str(session.user_id))

        if not user:
            return SendMessageResponse(
                success=False,
                response="",
                session_id=request.session_id,
                error="User not found"
            )

        if not session.agent_id:
            return SendMessageResponse(
                success=False,
                response="",
                session_id=request.session_id,
                error="No agent assigned to this session"
            )

        persona, instruction = AgentService.fetch_memory_agent_data(str(session.agent_id))
        if not instruction:
            return SendMessageResponse(
                success=False,
                response="",
                session_id=request.session_id,
                error="Memory agent not found"
            )

        llm_client = OpenAIClientAdapter(api_key=os.getenv("OPENAI_API_KEY"))

        chat_service = ChatService()
        memory_service = MemoryService(llm_client=llm_client)
        session_service = SessionService()
        prompt_builder = PromptBuilder()

        agent = AgentService(
            persona=persona,
            instruction=instruction,
            model="gpt-4o",
            agent_id=str(session.agent_id),
            user=user,
            llm_client=llm_client,
            memory_service=memory_service,
            chat_service=chat_service,
            session_service=session_service,
            user_service=user_service,
            prompt_builder=prompt_builder
        )

        logger.info(f'Running agent with input: {user_message}')
        response = agent.run(user_message, request.session_id)
        logger.info(f'Agent response: {response}')

        message_id = None
        try:
            message_id = memory_service.store_message(
                chat_session_id=session_id,
                role="user",
                content=request.message
            )
        except Exception as e:
            logger.warning(f"Could not store user message: {e}")

        try:
            memory_service.store_message(
                chat_session_id=session_id,
                role="assistant",
                content=response
            )
        except Exception as e:
            logger.warning(f"Could not store assistant response: {e}")

        return SendMessageResponse(
            success=True,
            response=response,
            session_id=request.session_id,
            message_id=str(message_id) if message_id else None
        )

    except Exception as e:
        logger.error(f"Error in send_message_to_agent: {e}")
        return SendMessageResponse(
            success=False,
            response="",
            session_id=request.session_id,
            error=str(e)
        )