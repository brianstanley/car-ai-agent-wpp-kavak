"""
Seeders for creating test data in the database.
"""

import logging

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from kavak_chatbot.models.schemas.agent import Agent
from db.config import Config
from kavak_chatbot.models import Persona
from kavak_chatbot.prompts.prompt_manager import prompt_manager
from logging_config import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

# Fixed IDs for testing
TEST_PERSONA_ID = "11111111-1111-1111-1111-111111111111"
TEST_AGENT_ID   = "22222222-2222-2222-2222-222222222222"
TEST_USER_ID    = "33333333-3333-3333-3333-333333333333"


class DatabaseSeeder:
    """Seeder for creating test data."""

    def __init__(self):
        self.connection_string = Config.DATABASE_URL

    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)

    def create_car_sales_persona(self) -> Persona:
        """Create a car sales persona."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if persona already exists
                    cursor.execute(
                        "SELECT id, name, role, goals, background "
                        "FROM personas WHERE id = %s",
                        (TEST_PERSONA_ID,)
                    )
                    persona_data = cursor.fetchone()

                    if persona_data is not None:
                        print("✅ Car sales persona already exists")
                        return Persona(
                            id=persona_data['id'],
                            name=persona_data['name'],
                            role=persona_data['role'],
                            goals=persona_data.get('goals'),
                            background=persona_data.get('background')
                        )

                    # Create new persona with fixed ID
                    cursor.execute("""
                        INSERT INTO personas (id, name, role, goals, background)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, name, role, goals, background
                    """, (
                        TEST_PERSONA_ID,
                        'Carlos',
                        'Representante de ventas de Kavak',
                        'Ayudar a cada cliente a encontrar el auto seminuevo ideal de manera fácil y confiable',
                        'Formado en el equipo de ventas de Kavak, con 5 años de experiencia asesorando a clientes, experto en catálogo de autos certificados y planes de financiamiento.'
                    ))
                    persona_data = cursor.fetchone()
                    conn.commit()
                    print("✅ Car sales persona created successfully")
                    return Persona(
                        id=persona_data['id'],
                        name=persona_data['name'],
                        role=persona_data['role'],
                        goals=persona_data['goals'],
                        background=persona_data['background']
                    )

        except Exception as e:
            print(f"❌ Error creating car sales persona: {e}")
            raise

    def create_car_sales_agent(self) -> Agent:
        """Create a car sales MemAgent."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Ensure persona exists
                    persona = self.create_car_sales_persona()

                    # Check if agent already exists
                    cursor.execute(
                        "SELECT id, instruction, application_mode, persona_id, tools "
                        "FROM agents WHERE id = %s",
                        (TEST_AGENT_ID,)
                    )
                    agent_data = cursor.fetchone()

                    if agent_data:
                        print("✅ Car sales agent already exists")
                        return Agent(
                            id=agent_data['id'],
                            instruction=agent_data['instruction'],
                            application_mode=agent_data['application_mode'],
                            persona_id=agent_data.get('persona_id'),
                            tools=agent_data.get('tools')
                        )

                    # Create new agent using prompt from file
                    instruction = prompt_manager.get_car_sales_agent_prompt()

                    cursor.execute("""
                        INSERT INTO agents (id, instruction, application_mode, persona_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, instruction, application_mode, persona_id, tools
                    """, (
                        TEST_AGENT_ID,
                        instruction,
                        "assistant",
                        str(persona.id)
                    ))
                    agent_data = cursor.fetchone()
                    conn.commit()
                    print("✅ Car sales agent created successfully")
                    return Agent(
                        id=agent_data['id'],
                        instruction=agent_data['instruction'],
                        application_mode=agent_data['application_mode'],
                        persona_id=agent_data['persona_id'],
                        tools=agent_data['tools']
                    )

        except Exception as e:
            print(f"❌ Error creating car sales agent: {e}")
            raise

    def create_test_user(self) -> dict:
        """Create a test user with phone_number '1111'."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check by phone_number first
                    cursor.execute(
                        "SELECT id, phone_number FROM users WHERE phone_number = %s",
                        ("1111",)
                    )
                    existing_user = cursor.fetchone()

                    if existing_user:
                        return existing_user
                    else:
                        # Create new user with the fixed ID
                        cursor.execute("""
                            INSERT INTO users (id, phone_number)
                            VALUES (%s, %s)
                            RETURNING id, phone_number
                        """, (TEST_USER_ID, "1111"))
                        user = cursor.fetchone()
                        conn.commit()
                        print("✅ Test user created successfully")
                        return user

        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            raise



    def run_seeders(self):
        """Run all seeders."""
        print("🌱 Running database seeders...")
        print("=" * 50)
        try:
            agent = self.create_car_sales_agent()
            user = self.create_test_user()

            print("\n📊 Seeder Results:")
            print(f"  - Agent ID:            {agent.id}")
            print(f"  - User ID:             {user['id']}")
            print(f"  - Application Mode:    {agent.application_mode}")
            print(f"  - Persona ID:          {agent.persona_id}")
            print(f"  - Tools:               {agent.tools}")
            print("\n🎉 All seeders completed successfully!")
            return agent

        except Exception as e:
            print(f"❌ Seeder failed: {e}")
            raise


def main():
    """Main function to run seeders."""
    try:
        seeder = DatabaseSeeder()
        return seeder.run_seeders()
    except Exception as e:
        print(f"❌ Failed to run seeders: {e}")
        return None


if __name__ == "__main__":
    main()
