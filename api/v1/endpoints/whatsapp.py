"""
WhatsApp endpoints for handling webhooks and messaging.
"""

import os
import logging
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
from    twilio.rest import Client

from services.user_service import UserService
from services.chat_service import ChatService
from services.memory_service import MemoryService
from services.agent_service import AgentService
from services.prompt_builder import PromptBuilder
from models.db.agent import AgentDB
from models.db.persona import PersonaDB
from models import Persona
from db.session import SessionLocal
from uuid import UUID

# Configure logging
logger = logging.getLogger(__name__)

# Constants
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_PHONE_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
MEMORY_AGENT_ID = "22222222-2222-2222-2222-222222222222"

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


# Remove the duplicate function - use AgentService.fetch_memory_agent_data instead


def parse_whatsapp_message(body: str, from_number: str) -> tuple[str, str]:
    """
    Parse WhatsApp message to extract user input and phone number.

    Args:
        body: The message body from WhatsApp
        from_number: The sender's phone number

    Returns:
        tuple: (user_input, phone_number)
    """
    # Remove 'whatsapp:' prefix if present
    phone_number = from_number.replace('whatsapp:', '')

    # Clean the phone number (remove any non-digit characters except +)
    phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')

    # If no country code, assume it's a Mexican number
    if not phone_number.startswith('+'):
        phone_number = '+52' + phone_number

    # Return the phone number without whatsapp: prefix (respond function will add it)
    return body.strip(), phone_number


def respond(to_number: str, message: str) -> None:
    """Send a message via Twilio WhatsApp"""
    try:
        # Ensure both numbers are in WhatsApp format
        if not to_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{to_number}"

        # Ensure from number is in WhatsApp format
        if not TWILIO_WHATSAPP_PHONE_NUMBER:
            raise ValueError("TWILIO_WHATSAPP_PHONE_NUMBER environment variable is not set")

        # Make sure the from number has the whatsapp: prefix
        if not TWILIO_WHATSAPP_PHONE_NUMBER.startswith('whatsapp:'):
            from_whatsapp_number = f"whatsapp:{TWILIO_WHATSAPP_PHONE_NUMBER}"
        else:
            from_whatsapp_number = TWILIO_WHATSAPP_PHONE_NUMBER

        # Log configuration for debugging
        logger.info(f"Twilio Account SID: {TWILIO_ACCOUNT_SID[:10] if TWILIO_ACCOUNT_SID else 'None'}...")
        logger.info(f"From WhatsApp Number: {from_whatsapp_number}")
        logger.info(f"To WhatsApp Number: {to_number}")

        # Create Twilio client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Send the message
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
    """
    WhatsApp webhook endpoint to handle incoming messages.
    """
    try:
        # 1) Log the request information
        logger.info(f'WhatsApp endpoint triggered...')
        logger.info(f'Request: {request}')
        logger.info(f'Body: {Body}')
        logger.info(f'From: {From}')

        # 2) Parse the number and query
        user_input, phone_number = parse_whatsapp_message(Body, From)
        logger.info(f'Parsed - Phone: {phone_number}, Input: {user_input}')

        # 3) Initialize services
        user_service = UserService()
        chat_service = ChatService()
        memory_service = MemoryService()
        openai_client = OpenAI()
        prompt_builder = PromptBuilder()

        # 4) Create or get existing chat session
        user = user_service.get_or_create_user(phone_number)
        session_info = chat_service.initialize_chat(phone_number)
        chat_session_id = str(session_info['session'].id)

        logger.info(f'User: {user.phone_number} (ID: {user.id})')
        logger.info(f'Session: {chat_session_id}')

        # 5) Fetch memory agent data
        persona, instruction = AgentService.fetch_memory_agent_data(MEMORY_AGENT_ID)
        if not instruction:
            logger.error("Could not fetch memory agent data")
            return JSONResponse(
                content={"error": "Memory agent not found"},
                status_code=500
            )

        # 6) Initialize AgentService
        agent = AgentService(
            persona=persona,
            instruction=instruction,
            model="gpt-4o",
            memory_agent_i=MEMORY_AGENT_ID,
            user=user,
            openai_client=openai_client,
            memory_service=memory_service,
            chat_service=chat_service,
            user_service=user_service,
            prompt_builder=prompt_builder
        )

        # 7) Run the agent and get response
        logger.info(f'Running agent with input: {user_input}')
        response = agent.run(user_input, chat_session_id)
        logger.info(f'Agent response: {response}')

        # 8) Send response back to WhatsApp
        try:
            respond(phone_number, response)
            logger.info(f'Response sent to WhatsApp: {phone_number}')
        except Exception as e:
            logger.error(f'Failed to send WhatsApp response: {e}')
            # Still return success but log the error

        # Return the response
        return JSONResponse(
            content={
                "success": True,
                "response": response,
                "session_id": chat_session_id,
                "user_id": str(user.id)
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