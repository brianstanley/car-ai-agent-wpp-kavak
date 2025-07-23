import logging
import os
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor

from kavak_chatbot.models.schemas.agent import Agent
from db.config import Config
from kavak_chatbot.models import Persona
from kavak_chatbot.prompts.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

DEFAULT_KAVAK_AGENT_ID = os.getenv("DEFAULT_KAVAK_AGENT_ID")
DEFAULT_DEMO_PHONE_NUMBER = os.getenv("DEFAULT_DEMO_PHONE_NUMBER")

def get_connection():
    return psycopg2.connect(Config.DATABASE_URL)

def create_car_sales_persona():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, name, role, goals, background "
                    "FROM personas WHERE name = %s AND role = %s",
                    ('Carlos', 'Representante de ventas de Kavak')
                )
                persona_data = cursor.fetchone()
                if persona_data is not None:
                    logger.info("✅ Car sales persona already exists")
                    return Persona(
                        id=persona_data['id'],
                        name=persona_data['name'],
                        role=persona_data['role'],
                        goals=persona_data.get('goals'),
                        background=persona_data.get('background')
                    )
                persona_id = str(uuid4())
                cursor.execute("""
                    INSERT INTO personas (id, name, role, goals, background)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, name, role, goals, background
                """, (
                    persona_id,
                    'Carlos',
                    'Representante de ventas de Kavak',
                    'Ayudar a cada cliente a encontrar el auto seminuevo ideal de manera fácil y confiable',
                    'Formado en el equipo de ventas de Kavak, con 5 años de experiencia asesorando a clientes, experto en catálogo de autos certificados y planes de financiamiento.'
                ))
                persona_data = cursor.fetchone()
                conn.commit()
                logger.info(f"✅ Car sales persona created successfully with ID: {persona_id}")
                return Persona(
                    id=persona_data['id'],
                    name=persona_data['name'],
                    role=persona_data['role'],
                    goals=persona_data['goals'],
                    background=persona_data['background']
                )
    except Exception as e:
        logger.info(f"❌ Error creating car sales persona: {e}")
        raise

def create_car_sales_agent():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                persona = create_car_sales_persona()
                cursor.execute(
                    "SELECT id, instruction, application_mode, persona_id, tools "
                    "FROM agents WHERE id = %s",
                    (DEFAULT_KAVAK_AGENT_ID,)
                )
                agent_data = cursor.fetchone()
                if agent_data:
                    logger.info("✅ Car sales agent already exists")
                    return Agent(
                        id=agent_data['id'],
                        instruction=agent_data['instruction'],
                        application_mode=agent_data['application_mode'],
                        persona_id=agent_data.get('persona_id'),
                        tools=agent_data.get('tools')
                    )
                instruction = prompt_manager.get_car_sales_agent_prompt()
                cursor.execute("""
                    INSERT INTO agents (id, instruction, application_mode, persona_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, instruction, application_mode, persona_id, tools
                """, (
                    DEFAULT_KAVAK_AGENT_ID,
                    instruction,
                    "assistant",
                    str(persona.id)
                ))
                agent_data = cursor.fetchone()
                conn.commit()
                logger.info(f"Car sales agent created successfully with ID: {DEFAULT_KAVAK_AGENT_ID}")
                return Agent(
                    id=agent_data['id'],
                    instruction=agent_data['instruction'],
                    application_mode=agent_data['application_mode'],
                    persona_id=agent_data['persona_id'],
                    tools=agent_data['tools']
                )
    except Exception as e:
        logger.info(f"❌ Error creating car sales agent: {e}")
        raise

def create_test_user():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, phone_number FROM users WHERE phone_number = %s",
                    (DEFAULT_DEMO_PHONE_NUMBER,)
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    logger.info("✅ Test user already exists")
                    return existing_user
                else:
                    user_id = str(uuid4())
                    cursor.execute("""
                        INSERT INTO users (id, phone_number)
                        VALUES (%s, %s)
                        RETURNING id, phone_number
                    """, (user_id, "1111"))
                    user = cursor.fetchone()
                    conn.commit()
                    logger.info(f"✅ Test user created successfully with ID: {user_id}")
                    return user
    except Exception as e:
        logger.info(f"❌ Error creating test user: {e}")
        raise

def run_seeders():
    """Run all seeders."""
    logger.info("🌱 Running database seeders...")
    logger.info("=" * 50)
    try:
        agent = create_car_sales_agent()
        user = create_test_user()
        print("\n📊 Seeder Results:")
        print(f"  - Agent ID:            {agent.id}")
        print(f"  - User ID:             {user['id']}")
        print(f"  - Application Mode:    {agent.application_mode}")
        print(f"  - Persona ID:          {agent.persona_id}")
        print("\n🎉 All seeders completed successfully!")
        return agent
    except Exception as e:
        logger.info(f"❌ Seeder failed: {e}")
        raise

def main():
    try:
        return run_seeders()
    except Exception as e:
        logger.info(f"❌ Failed to run seeders: {e}")
        return None

if __name__ == "__main__":
    main()
