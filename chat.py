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

# Cargar variables de entorno
load_dotenv()


def fetch_memory_agent_data(agent_id: str) -> Tuple[Optional[Persona], Optional[str]]:
    try:
        with SessionLocal() as session:
            # Fetch agent with persona relationship
            agent = session.query(AgentDB).filter(AgentDB.id == UUID(agent_id)).first()

            if not agent:
                print(f"❌ Agent with ID {agent_id} not found")
                return None, None

            # Fetch persona if it exists
            persona = None
            if agent.persona_id is not None:
                persona_db = session.query(PersonaDB).filter(PersonaDB.id == agent.persona_id).first()
                if persona_db is not None:
                    persona = Persona(
                        id=UUID(str(persona_db.id)),
                        name=str(persona_db.name),
                        role=str(persona_db.role),
                        goals=str(persona_db.goals) if persona_db.goals is not None else None,
                        background=str(persona_db.background) if persona_db.background is not None else None
                    )

            print(f"✅ Fetched agent data:")
            print(f"   - Agent ID: {agent.id}")
            print(f"   - Application Mode: {agent.application_mode}")
            print(f"   - Persona: {persona.name if persona else 'None'}")
            instruction_val = str(agent.instruction) if agent.instruction is not None else None
            print(f"   - Instruction length: {len(instruction_val) if instruction_val else 0} characters")

            return persona, instruction_val

    except Exception as e:
        print(f"❌ Error fetching memory agent data: {e}")
        return None, None


def main():
    print("🤖 Chat con MemAgent")
    print("=" * 60)
    print("Type your messages and press Enter to chat.")
    print("Commands:")
    print("  /quit or /exit - Exit the chat")
    print("=" * 60)

    # Inicializar servicios y dependencias
    user_service = UserService()
    chat_service = ChatService()
    memory_service = MemoryService()
    openai_client = OpenAI()
    prompt_builder = PromptBuilder()
    # Si tienes un UserManager personalizado, instáncialo aquí

    # Inicializar usuario y sesión (usuario fijo para demo)
    user = user_service.get_or_create_user("1111")
    session_info = chat_service.initialize_chat("1111")
    chat_session_id = str(session_info['session'].id)
    memory_agent_id = "22222222-2222-2222-2222-222222222222"  # ID fijo de MemAgent del seeder

    # Fetch persona and instruction for the memory agent
    persona, instruction = fetch_memory_agent_data(memory_agent_id)
    if not instruction:
        print("❌ Could not fetch memory agent data. Exiting.")
        return

    agent = AgentService(
        persona=persona,
        instruction=instruction,
        model="gpt-4o",
        memory_agent_i=memory_agent_id,
        user=user,
        openai_client=openai_client,
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