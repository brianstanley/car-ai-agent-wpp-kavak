"""
Chat interactivo usando MemAgentService para gestionar la conversación.
"""

import logging
import os

from dotenv import load_dotenv

from kavak_chatbot.services import UserService, ChatService, MemoryService, AgentService
from kavak_chatbot.services.llm_openai_adapter import OpenAIClientAdapter
from kavak_chatbot.services.prompt_builder import PromptBuilder
from kavak_chatbot.utils import OpenAITokenizerWrapper, truncate_text_to_max_tokens
from logging_config import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)


def main():
    print("🤖 Chat con Agente de Kavak: carlos")
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
        llm_client=llm_client,
        memory_service=memory_service,
        chat_service=chat_service,
        user_service=user_service,
        prompt_builder=prompt_builder
    )

    print(f"👤 Usuario: {user.phone_number} (ID: {user.id})")
    print(f"💬 Sesión: {chat_session_id}")
    print(f"🧠 Bot ID: {memory_agent_id}")

    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
                print("👋 Goodbye!")
                break
            if not user_input:
                print("Por favor, escribe un mensaje o comando.")
                continue

            MAX_USER_QUERY_TOKENS = int(os.getenv("MAX_USER_QUERY_TOKENS", 1024))
            tokenizer = OpenAITokenizerWrapper(model_name="cl100k_base")
            num_tokens = len(tokenizer.tokenize(user_input))
            if num_tokens > MAX_USER_QUERY_TOKENS:
                user_input = truncate_text_to_max_tokens(user_input, MAX_USER_QUERY_TOKENS, model_name="cl100k_base")
                print(f"Tu mensaje fue muy largo y ha sido truncado a los primeros {MAX_USER_QUERY_TOKENS} tokens.")

            response = agent.run(user_input, chat_session_id)
            print(f"🤖 Assistant: {response}")
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()