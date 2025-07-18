#!/usr/bin/env python3
"""
Seeders for creating test data in the database.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from datetime import datetime, UTC, timedelta

from models.schemas.agent import Agent
from db.config import Config
from models import Persona

# Fixed IDs for testing
TEST_PERSONA_ID = "11111111-1111-1111-1111-111111111111"
TEST_AGENT_ID   = "22222222-2222-2222-2222-222222222222"
TEST_USER_ID    = "33333333-3333-3333-3333-333333333333"
TEST_CHAT_SESSION_ID = "44444444-4444-4444-4444-444444444444"


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

                    if persona_data:
                        print("✅ Car sales persona already exists")
                        return Persona(
                            id=persona_data['id'],
                            name=persona_data['name'],
                            role=persona_data['role'],
                            goals=persona_data['goals'],
                            background=persona_data['background']
                        )

                    # Create new persona with fixed ID
                    cursor.execute("""
                        INSERT INTO personas (id, name, role, goals, background)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, name, role, goals, background
                    """, (
                        TEST_PERSONA_ID,
                        'Carlos',
                        'representante de ventas',
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
                            persona_id=agent_data['persona_id'],
                            tools=agent_data['tools']
                        )

                    # Create new agent
                    instruction = """
                        1. Saluda por su nombre y muestra empatía.  
                        2. Recuérdale la propuesta de valor de Kavak:  
                           - Autos seminuevos **certificados**  
                           - **Garantía** y revisión de calidad  
                           - **Prueba de manejo** sin costo  
                        3. Haz preguntas para entender su presupuesto y estilo de vida.  
                        4. Ofrece opciones claras, con precios y plazos de financiamiento.  
                        5. **No repitas** datos o preferencias que ya conoces:  
                           - Si el cliente mencionó antes que prefiere un SUV, **guárdalo** y úsalo sin volver a preguntarlo ni enunciarlo.  
                           - No digas “Sé que te gustan los autos rojos” si ya lo mencionaste; simplemente filtra tu recomendación según ese dato.  
                        6. **Evita repetir saludos**:  
                           - Si en los últimos turnos ya hubo un “hola”, “buenos días”, etc., **no saludes de nuevo**; continúa la conversación de manera natural.  
                        7. Evita respuestas genéricas: personaliza cada recomendación.  
                        8. Termina siempre preguntando si hay más dudas.
                        9. Si no sabes su nombre preguntaselo y guárdalo para futuras conversaciones.
                        10. Trata de sonar humano. Si guardas preferencias, no le informes al usuario que lo haces, simplemente actúa como un humano que recuerda detalles de la conversación anterior.
                    """

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
                    # Check by ID
                    cursor.execute(
                        "SELECT id, phone_number FROM users WHERE id = %s",
                        (TEST_USER_ID,)
                    )
                    user = cursor.fetchone()
                    if user:
                        print("✅ Test user already exists")
                        return user

                    # Otherwise check by phone_number
                    cursor.execute(
                        "SELECT id, phone_number FROM users WHERE phone_number = %s",
                        ("1111",)
                    )
                    existing_user = cursor.fetchone()
                    if existing_user:
                        cursor.execute("""
                            UPDATE users SET id = %s WHERE phone_number = %s
                            RETURNING id, phone_number
                        """, (TEST_USER_ID, "1111"))
                    else:
                        cursor.execute("""
                            INSERT INTO users (id, phone_number)
                            VALUES (%s, %s)
                            RETURNING id, phone_number
                        """, (TEST_USER_ID, "1111"))
                    user = cursor.fetchone()
                    conn.commit()
                    print("✅ Test user created/updated")
                    return user

        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            raise

    def create_chat_session_with_conversation(self, agent_id, user_id):
        """Create a chat session and seed with 4 example messages."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO chat_sessions (id, agent_id, user_id, started_at)
                        VALUES (%s, %s, %s, %s)
                    """, (TEST_CHAT_SESSION_ID, str(agent_id), str(user_id), datetime.now(UTC)))
                    print("✅ Chat session created")

                    messages = [
                        ("user",      "Hola, soy Brian y estoy buscando un coche nuevo."),
                        ("assistant", "¡Hola Brian! ¿Qué tipo de coche te interesa?"),
                        ("user",      "Me gustaría algo familiar y seguro. ¿Qué opciones tienes?"),
                        ("assistant", "Tenemos varios modelos familiares y seguros. ¿Prefieres SUV o sedán?")
                    ]
                    for role, content in messages:
                        cursor.execute("""
                            INSERT INTO conversations_memory (
                              id, chat_session_id, role, content, created_at, embedded
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            str(uuid4()),
                            TEST_CHAT_SESSION_ID,
                            role,
                            content,
                            datetime.now(UTC),
                            False
                        ))
                    conn.commit()
                    print("✅ Example conversation added")
                    return TEST_CHAT_SESSION_ID

        except Exception as e:
            print(f"❌ Error creating chat session/conversation: {e}")
            raise

    def create_summaries_for_chat_session(self, chat_session_id):
        """Create two summary entries for the given chat session."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    now = datetime.now(UTC)
                    summaries = [
                        (
                            str(uuid4()),
                            chat_session_id,
                            "Brian es fanático de los autos negros.",
                            now,
                            now - timedelta(days=1),
                            now - timedelta(days=1) + timedelta(hours=1),
                            None
                        ),
                        (
                            str(uuid4()),
                            chat_session_id,
                            "Al usuario Brian le gustan los autos hatchback y prefiere pagar al contado.",
                            now + timedelta(days=1),
                            now,
                            now + timedelta(hours=1),
                            None
                        )
                    ]
                    for s in summaries:
                        cursor.execute("""
                            INSERT INTO summaries_memory (
                              id, chat_session_id, text, created_at,
                              period_start, period_end, embedding
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, s)
                    conn.commit()
                    print("✅ Summaries_memory entries added")
        except Exception as e:
            print(f"❌ Error creating summaries_memory: {e}")
            raise

    def run_seeders(self):
        """Run all seeders."""
        print("🌱 Running database seeders...")
        print("=" * 50)
        try:
            agent = self.create_car_sales_agent()
            user = self.create_test_user()
            chat_session_id = self.create_chat_session_with_conversation(agent.id, user['id'])
            self.create_summaries_for_chat_session(chat_session_id)

            print("\n📊 Seeder Results:")
            print(f"  - Agent ID:            {agent.id}")
            print(f"  - User ID:             {user['id']}")
            print(f"  - Application Mode:    {agent.application_mode}")
            print(f"  - Persona ID:          {agent.persona_id}")
            print(f"  - Tools:               {agent.tools}")
            print(f"  - Chat Session ID:     {chat_session_id}")
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
