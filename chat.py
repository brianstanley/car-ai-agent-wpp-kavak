#!/usr/bin/env python3
"""
Chat interactivo usando MemAgentService para gestionar la conversación.
"""

from dotenv import load_dotenv
from typing import Tuple, Optional
from uuid import UUID

from db.session import SessionLocal
from models.db.agent import AgentDB
from models.db.persona import PersonaDB
from models import Persona
from services.prompt_builder import PromptBuilder
from services.user_service import UserService
from services.chat_service import ChatService
from services.memory_service import MemoryService
from services.agent_service import AgentService
from openai import OpenAI
from services.llm_openai_adapter import OpenAIClientAdapter

# Cargar variables de entorno
load_dotenv()


# Remove the duplicate function - use AgentService.fetch_memory_agent_data instead


def main():
    print("🤖 Chat con MemAgent")
    print("=" * 60)
    print("Type your messages and press Enter to chat.")
    print("Commands:")
    print("  /quit or /exit - Exit the chat")
    print("=" * 60)

    # Inicializar servicios y dependencias
    llm_client = OpenAIClientAdapter()
    user_service = UserService()
    chat_service = ChatService()
    memory_service = MemoryService(llm_client=llm_client)
    prompt_builder = PromptBuilder()
    # Si tienes un UserManager personalizado, instáncialo aquí

    # Inicializar usuario y sesión (usuario fijo para demo)
    user = user_service.get_or_create_user("1111")
    session_info = chat_service.initialize_chat("1111")
    chat_session_id = str(session_info['session'].id)
    memory_agent_id = "22222222-2222-2222-2222-222222222222"  # ID fijo de MemAgent del seeder

    # Fetch persona and instruction for the memory agent
    persona, instruction = AgentService.fetch_memory_agent_data(memory_agent_id)
    if not instruction:
        print("❌ Could not fetch memory agent data. Exiting.")
        return

    agent = AgentService(
        persona=persona,
        instruction=instruction,
        model="gpt-4o",
        memory_agent_i=memory_agent_id,
        user=user,
        llm_client=llm_client,  # Cambiado aquí
        memory_service=memory_service,
        chat_service=chat_service,
        user_service=user_service,
        prompt_builder=prompt_builder
    )

    print(f"👤 Usuario: {user.phone_number} (ID: {user.id})")
    print(f"💬 Sesión: {chat_session_id}")
    print(f"🧠 MemAgent: {memory_agent_id}")

    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
                print("👋 Goodbye!")
                break
            if not user_input:
                print("Por favor, escribe un mensaje o comando.")
                continue

            print("🤖 Assistant: ", end="", flush=True)
            response = agent.run(user_input, chat_session_id)
            print(f"Agente: ", response)
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()