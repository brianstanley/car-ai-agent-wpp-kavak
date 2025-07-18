#!/usr/bin/env python3
"""
Example of how to use the KavakInfoSearchTool in the context of the agent.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent_service import AgentService
from services.user_service import UserService
from services.memory_service import MemoryService
from services.chat_service import ChatService
from services.prompt_builder import PromptBuilder
from models.schemas.user import UserCreate
from openai import OpenAI

# Load environment variables
load_dotenv()

def create_test_user():
    """Create a test user for the example."""
    user_service = UserService()
    
    # Create a test user
    user_data = UserCreate(
        phone="1234567890",
        name="Usuario de Prueba",
        mail="test@example.com"
    )
    
    try:
        user = user_service.create_user(user_data)
        print(f"✅ Usuario de prueba creado: {user.id}")
        return user
    except Exception as e:
        print(f"⚠️ Usando usuario existente: {e}")
        # Try to get existing user
        return user_service.get_user_by_phone("1234567890")

def example_agent_with_kavak_info():
    """Example of using the agent with KavakInfoSearchTool."""
    print("🤖 Ejemplo de uso del agente con KavakInfoSearchTool")
    print("=" * 60)
    
    try:
        # Initialize services
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        memory_service = MemoryService()
        chat_service = ChatService()
        user_service = UserService()
        prompt_builder = PromptBuilder()
        
        # Create test user
        user = create_test_user()
        
        # Create a test chat session
        session = chat_service.create_session(user.phone)
        chat_session_id = str(session.id)
        
        print(f"💬 Chat session creada: {chat_session_id}")
        
        # Initialize agent service
        agent = AgentService(
            persona="Eres un asistente experto de Kavak que ayuda a los clientes con información sobre nuestros servicios, procesos de compra, y catálogo de vehículos.",
            instruction="Proporciona información clara y útil sobre Kavak. Usa las herramientas disponibles para buscar información específica cuando sea necesario.",
            user=user,
            model="gpt-4o",
            openai_client=client,
            memory_service=memory_service,
            chat_service=chat_service,
            user_service=user_service,
            prompt_builder=prompt_builder
        )
        
        # Test queries that should trigger the KavakInfoSearchTool
        test_queries = [
            "¿Cuál es la propuesta de valor de Kavak?",
            "¿Dónde están las sucursales de Kavak?",
            "¿Qué documentación necesito para comprar un auto?",
            "¿Cómo funciona el período de prueba?",
            "¿Cómo evalúan los vehículos en Kavak?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Consulta {i}: {query}")
            print(f"{'='*60}")
            
            try:
                response = agent.run(query, chat_session_id)
                print(f"🤖 Respuesta del agente:\n{response}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n✅ Ejemplo completado!")
        
    except Exception as e:
        print(f"❌ Error en el ejemplo: {e}")

def main():
    """Main function."""
    print("🚀 Ejemplo de KavakInfoSearchTool con AgentService")
    print("=" * 60)
    
    example_agent_with_kavak_info()

if __name__ == "__main__":
    main() 