"""
WhatsApp endpoints for handling webhooks and messaging.
"""

import os
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from twilio.rest import Client
from uuid import UUID

from kavak_chatbot.services import UserService, ChatService, MemoryService, AgentService
from kavak_chatbot.services.llm_openai_adapter import OpenAIClientAdapter
from kavak_chatbot.services.prompt_builder import PromptBuilder
from kavak_chatbot.utils import OpenAITokenizerWrapper, truncate_text_to_max_tokens

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_PHONE_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
DEFAULT_KAVAK_AGENT_ID = os.getenv("DEFAULT_KAVAK_AGENT_ID")

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

def parse_whatsapp_message(body: str, from_number: str) -> tuple[str, str]:
    phone_number = from_number.replace('whatsapp:', '')

    phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')

    if not phone_number.startswith('+'):
        phone_number = '+52' + phone_number

    return body.strip(), phone_number


def respond(to_number: str, message: str) -> None:
    try:
        if not to_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{to_number}"

        if not TWILIO_WHATSAPP_PHONE_NUMBER:
            raise ValueError("TWILIO_WHATSAPP_PHONE_NUMBER environment variable is not set")

        if not TWILIO_WHATSAPP_PHONE_NUMBER.startswith('whatsapp:'):
            from_whatsapp_number = f"whatsapp:{TWILIO_WHATSAPP_PHONE_NUMBER}"
        else:
            from_whatsapp_number = TWILIO_WHATSAPP_PHONE_NUMBER

        logger.info(f"Twilio Account SID: {TWILIO_ACCOUNT_SID[:10] if TWILIO_ACCOUNT_SID else 'None'}...")
        logger.info(f"From WhatsApp Number: {from_whatsapp_number}")
        logger.info(f"To WhatsApp Number: {to_number}")

        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message_obj = twilio_client.messages.create(
            body=message,
            from_=from_whatsapp_number,
            to=to_number
        )

        logger.info(f"Message sent successfully. SID: {message_obj.sid}")
        logger.info(f"To: {to_number}")
        logger.info(f"From: {from_whatsapp_number}")
        logger.info(f"Message: {message}")

    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(...),
    From: str = Form(...)
) -> JSONResponse:
    try:
        logger.info(f'WhatsApp endpoint triggered...')
        logger.info(f'Request: {request}')
        logger.info(f'Body: {Body}')
        logger.info(f'From: {From}')

        user_input, phone_number = parse_whatsapp_message(Body, From) # Parse the number and query

        MAX_USER_QUERY_TOKENS = int(os.getenv("MAX_USER_QUERY_TOKENS", 1024))
        tokenizer = OpenAITokenizerWrapper(model_name="cl100k_base")
        num_tokens = len(tokenizer.tokenize(user_input))
        if num_tokens > MAX_USER_QUERY_TOKENS:
            user_input = truncate_text_to_max_tokens(user_input, MAX_USER_QUERY_TOKENS, model_name="cl100k_base")

        llm_client = OpenAIClientAdapter(api_key=os.getenv("OPENAI_API_KEY"))

        user_service = UserService()
        chat_service = ChatService()
        memory_service = MemoryService(llm_client=llm_client)
        prompt_builder = PromptBuilder()

        session_info = chat_service.initialize_chat(phone_number, UUID(DEFAULT_KAVAK_AGENT_ID))
        user = session_info.user
        chat_session_id = str(session_info.session.id)

        logger.info(f'User: {user.phone_number} (ID: {user.id})')
        logger.info(f'Session: {chat_session_id}')

        persona, instruction = AgentService.fetch_memory_agent_data(DEFAULT_KAVAK_AGENT_ID)
        if not instruction:
            logger.error("Could not fetch memory agent data")
            return JSONResponse(
                content={"error": "Memory agent not found"},
                status_code=500
            )

        agent = AgentService(
            persona=persona,
            instruction=instruction,
            model="gpt-4o",
            agent_id=DEFAULT_KAVAK_AGENT_ID,
            user=user,
            llm_client=llm_client,
            memory_service=memory_service,
            chat_service=chat_service,
            user_service=user_service,
            prompt_builder=prompt_builder
        )

        logger.info(f'Running agent with input: {user_input}')
        response = agent.run(user_input, chat_session_id)
        logger.info(f'Agent response: {response}')

        try:
            respond(phone_number, response)
            logger.info(f'Response sent to WhatsApp: {phone_number}')
        except Exception as e:
            logger.error(f'Failed to send WhatsApp response: {e}')

        return JSONResponse(
            content={
                "success": True,
                "response": response,
                "session_id": chat_session_id,
                "user_id": str(session_info.user.id)
            }
        )

    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@router.post("/send")
async def send_whatsapp_message(
    to_number: str = Form(...),
    message: str = Form(...)
) -> JSONResponse:
    """Send a WhatsApp message manually."""
    try:
        respond(to_number, message)
        return JSONResponse(
            content={
                "success": True,
                "message": "WhatsApp message sent successfully",
                "to": to_number
            }
        )
    except Exception as e:
        logger.error(f"Error in send WhatsApp message: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )