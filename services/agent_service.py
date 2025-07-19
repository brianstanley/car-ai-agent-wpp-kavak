#!/usr/bin/env python3
"""
Memory Agent service for running agents with memory and conversation context.
"""
import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from services.memory_service import MemoryService
from services.chat_service import ChatService
from services.prompt_builder import PromptBuilder
from services.user_service import UserService
from tools import ExtractUserNameTool, CatalogSearchTool, CarFinancialTool, KavakInfoSearchTool
from models.db.agent import AgentDB
from models.db.persona import PersonaDB
from models import Persona
from db.session import SessionLocal

# Load environment variables
load_dotenv()

class AgentService:
    """Memory Agent for running agents with memory and conversation context."""

    def __init__(
        self,
        persona,
        instruction,
        user,
        model: str = "gpt-4o",
        memory_agent_i=None,
        *,
        openai_client: Optional[OpenAI] = None,
        memory_service: Optional[MemoryService] = None,
        chat_service: Optional[ChatService] = None,
        user_service: Optional[UserService] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize the memory agent service with required dependencies.

        Args:
            persona: The persona configuration
            instruction: The instruction for the agent
            user: The user object
            model: The OpenAI model to use
            memory_agent_i: Memory agent identifier
            openai_client: OpenAI client instance (injected)
            memory_service: Memory service instance (injected)
            chat_service: Chat service instance (injected)
            user_service: User service instance (injected)
        """
        # Validate required environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Error: OPENAI_API_KEY not found in environment variables")
            sys.exit(1)

        # Use injected dependencies or create defaults
        self.client = openai_client or OpenAI(api_key=api_key)
        self.memory_service = memory_service or MemoryService()
        self.chat_service = chat_service or ChatService()
        self.user_service = user_service
        self.prompt_builder = prompt_builder

        # Configuration
        self.model = model
        self.persona = persona
        self.instruction = instruction
        self.memory_agent_i = memory_agent_i
        self.user = user

        # Initialize tools
        self.extract_user_name_tool = ExtractUserNameTool(user_service=self.user_service)
        self.catalog_search_tool = CatalogSearchTool(openai_client=self.client)
        self.car_financial_tool = CarFinancialTool()
        self.kavak_info_search_tool = KavakInfoSearchTool(openai_client=self.client)

    @staticmethod
    def fetch_memory_agent_data(agent_id: str) -> Tuple[Optional[Persona], Optional[str]]:
        """
        Fetch memory agent data from database.

        Args:
            agent_id: The agent ID to fetch

        Returns:
            Tuple of (Persona, instruction) or (None, None) if not found
        """
        try:
            with SessionLocal() as session:
                # Fetch agent with persona relationship
                agent = session.query(AgentDB).filter(AgentDB.id == UUID(agent_id)).first()

                if not agent:
                    print(f"Agent with ID {agent_id} not found")
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

                print(f"Fetched agent data:")
                print(f"   - Agent ID: {agent.id}")
                print(f"   - Application Mode: {agent.application_mode}")
                print(f"   - Persona: {persona.name if persona else 'None'}")
                instruction_val = str(agent.instruction) if agent.instruction is not None else None
                print(f"   - Instruction length: {len(instruction_val) if instruction_val else 0} characters")

                return persona, instruction_val

        except Exception as e:
            print(f"Error fetching memory agent data: {e}")
            return None, None

    def run(self, query: str, chat_session_id: str) -> str:
        """
        Run the agent with the given query.
        Parameters:
            query (str): The query to run the agent with.
            chat_session_id (str): The conversation id to use.
        Returns:
            str: The response from the agent.
        """
        try:
            print(f"🤖 Running MemAgent with query: {query}")
            print(f"🧠 Memory Agent ID: {self.memory_agent_i}")
            print(f"💬 Chat Session ID: {chat_session_id}")

            # 1) Prepare memory and conversation IDs
            memory_id = self._prepare_memory_and_conversation_ids(chat_session_id)

            # 2) Build augmented query using PromptBuilder
            print("\n2️⃣ Building augmented query...")
            messages = self._build_prompt_messages(query, memory_id)


            # LOG DEL PROMPT QUE SE VA A ENVIAR AL LLM
            print("\n📝 PROMPT QUE SE ENVÍA AL LLM:")
            for i, msg in enumerate(messages):
                print(f"[{i}] {msg['role'].upper()}\n{msg['content']}\n{'-'*40}")

            # 5) Record user's query in memory
            print("\n5️⃣ Recording user query in memory...")
            self._record_user_query(query, chat_session_id)


            # 6) Get response from OpenAI
            print("\n6️⃣ Getting response from OpenAI...")
            # response = self._get_openai_response(messages)
            response = self._execute_main_loop(
                messages=messages,
                query=query,
                memory_id=memory_id,
                conversation_id=chat_session_id,
                user_id=self.user.id
            )

            # 7) Record assistant response in memory
            if response:
                self._record_assistant_response(response, chat_session_id)

            return response or "❌ No response received from agent"

        except Exception as e:
            error_msg = f"❌ Error running MemAgent: {e}"
            print(error_msg)
            return error_msg

    def _prepare_memory_and_conversation_ids(self, chat_session_id: str) -> str:
        """
        Prepare memory and conversation IDs for the agent run.
        Parameters:
            chat_session_id (str): The chat session ID.
        Returns:
            str: The prepared memory ID.
        """
        try:
            # Validate chat session exists
            chat_session_uuid = UUID(chat_session_id)

            # Get session from database to validate it exists using ChatService
            if self.chat_service:
                # Try to get the session using ChatService
                session_info = self.chat_service.get_user_session("1111")  # Using default phone for now
                if session_info and session_info.get('session') and str(session_info['session'].id) == chat_session_id:
                    session = session_info['session']
                else:
                    # If not found via ChatService, try to get it directly from database
                    from db.session import SessionLocal
                    from models.db.chat_session import ChatSessionDB

                    with SessionLocal() as db_session:
                        session = db_session.query(ChatSessionDB).filter(ChatSessionDB.id == chat_session_uuid).first()
                        if session:
                            print(f"   ✅ Chat session validated: {session.id}")
                        else:
                            raise ValueError(f"Chat session {chat_session_id} does not exist")
            else:
                # Fallback to direct database query if ChatService is not available
                from db.session import SessionLocal
                from models.db.chat_session import ChatSessionDB

                with SessionLocal() as db_session:
                    session = db_session.query(ChatSessionDB).filter(ChatSessionDB.id == chat_session_uuid).first()
                    if session:
                        print(f"   ✅ Chat session validated: {session.id}")
                    else:
                        raise ValueError(f"Chat session {chat_session_id} does not exist")

            # Use the chat_session_id as the memory_id for now
            memory_id = chat_session_id
            return memory_id

        except ValueError as e:
            print(f"   ❌ Validation error: {e}")
            raise
        except Exception as e:
            print(f"   ❌ Error preparing memory and conversation IDs: {e}")
            raise

    def _record_user_query(self, query: str, chat_session_id: str) -> None:
        """
        Record the user's query in memory.

        Parameters:
            query (str): The user's query.
            chat_session_id (str): The chat session ID.
        """
        try:
            self.memory_service.store_message(UUID(chat_session_id), "user", query)
        except Exception as e:
            print(f"   ⚠️ Warning: Could not record user query: {e}")

    def _record_assistant_response(self, response: str, chat_session_id: str) -> None:
        """
        Record the assistant's response in memory.

        Parameters:
            response (str): The assistant's response.
            chat_session_id (str): The chat session ID.
        """
        try:
            self.memory_service.store_message(UUID(chat_session_id), "assistant", response)
        except Exception as e:
            print(f"   ⚠️ Warning: Could not record assistant response: {e}")

    def _build_prompt_messages(self, query: str, memory_id: str) -> List[Dict[str, str]]:
        """
        Build prompt messages step by step, appending each component in order.

        Args:
            query: The user query
            memory_id: The memory ID to use

        Returns:
            List[Dict[str, str]]: Messages list for OpenAI API
        """
        messages = []
        # Step 1: Build system message with persona and instruction
        print("   📝 Step 1: Adding system message...")
        if self.prompt_builder:
            system_content = self.prompt_builder.add_system(self.persona, self.instruction).system_prompt
        else:
            # Fallback if prompt_builder is not available
            system_content = f"Eres un asistente experto de Kavak. {self.persona}\n\n{self.instruction}"

        # Step 1.5: Add user preferences to system message
        print("   📝 Step 1.5: Adding user preferences...")
        preferences_section = self._build_user_preferences_section()
        if preferences_section:
            system_content += f"\n\n{preferences_section}"

        messages.append({"role": "system", "content": system_content})

        # Step 2: Add conversation history as separate messages
        try:
            recent_messages = self.memory_service.get_last_n_messages(UUID(memory_id), n=10)
            history_count = 0

            for msg in recent_messages:
                role = msg['role']
                content = msg['content']
                if role == 'user':
                    messages.append({"role": "user", "content": content})
                    history_count += 1
                elif role == 'assistant':
                    messages.append({"role": "assistant", "content": content})
                    history_count += 1

            print(f"   ✅ Added {history_count} history messages")

        except Exception as e:
            print(f"   ⚠️ Warning: Could not add conversation history: {e}")

        # Step 3: Add current user query
        messages.append({"role": "user", "content": query})

        # Step 4: Return final array
        for i, msg in enumerate(messages):
            print(f"  [{i}] {msg['role'].upper()}: {msg['content'][:50]}...")

        return messages

    def _get_openai_response(self, messages: List[Any], tools: Optional[List[Dict]] = None) -> str:
        """
        Get response from OpenAI API.

        Parameters:
            messages (List[Any]): The messages to send to OpenAI.
            tools (Optional[List[Dict]]): Tools to use with the API call.

        Returns:
            str: The response from OpenAI.
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }

            if tools:
                kwargs["tools"] = tools

            completion = self.client.chat.completions.create(**kwargs)

            response = completion.choices[0].message.content
            if response is None:
                return "❌ No response received from OpenAI"

            return response

        except Exception as e:
            return f"❌ Error getting response from OpenAI: {e}"

    def _build_user_preferences_section(self) -> str:
        """
        Build a formatted string containing the user's preferences for inclusion in the system message.

        Returns:
            str: Formatted preferences section or empty string if no preferences
        """
        if not self.user or not self.user.preferences:
            return ""

        preferences = self.user.preferences
        if not preferences or not isinstance(preferences, dict):
            return ""

        # Build preferences section
        preferences_text = "PREFERENCIAS DEL USUARIO:\n"
        preferences_text += "=" * 50 + "\n"

        # Personal information
        if preferences.get('name'):
            preferences_text += f"Nombre: {preferences['name']}\n"
        if preferences.get('mail'):
            preferences_text += f"Email: {preferences['mail']}\n"
        if preferences.get('ine'):
            preferences_text += f"INE: {preferences['ine']}\n"

        # Vehicle preferences
        vehicle_prefs = []
        if preferences.get('make'):
            vehicle_prefs.append(f"Marca: {preferences['make']}")
        if preferences.get('model'):
            vehicle_prefs.append(f"Modelo: {preferences['model']}")
        if preferences.get('year'):
            vehicle_prefs.append(f"Año: {preferences['year']}")
        if preferences.get('version'):
            vehicle_prefs.append(f"Versión: {preferences['version']}")

        if vehicle_prefs:
            preferences_text += "Vehículo deseado:\n"
            for pref in vehicle_prefs:
                preferences_text += f"  - {pref}\n"

        # Price and mileage ranges
        if preferences.get('price') and isinstance(preferences['price'], list) and len(preferences['price']) == 2:
            min_price, max_price = preferences['price']
            preferences_text += f"Rango de precio: ${min_price:,} - ${max_price:,} USD\n"

        if preferences.get('km') and isinstance(preferences['km'], list) and len(preferences['km']) == 2:
            min_km, max_km = preferences['km']
            if min_km == 0:
                preferences_text += f"Kilometraje: Nuevo (0 km) hasta {max_km:,} km\n"
            else:
                preferences_text += f"Kilometraje: {min_km:,} - {max_km:,} km\n"

        # Features
        features = []
        if preferences.get('bluetooth') is True:
            features.append("Bluetooth")
        if preferences.get('car_play') is True:
            features.append("Apple CarPlay")

        if features:
            preferences_text += f"Características deseadas: {', '.join(features)}\n"

        # Other preferences
        if preferences.get('other_preferences'):
            preferences_text += f"Otras preferencias: {preferences['other_preferences']}\n"

        preferences_text += "=" * 50 + "\n"

        print(f"   ✅ Added user preferences to system message")
        return preferences_text

    def _merge_preferences(self, user_id, new_preferences: dict):
        """
        Merges new preferences into the user's existing preferences in the database.
        Parameters:
            user_id (str): The ID of the user whose preferences are being updated.
            new_preferences (dict): The new preferences to merge into the user's existing preferences.
        """
        print(f"🔄 Updating preferences for user {user_id}...")
        try:
            if self.user_service:
                self.user_service.update_preferences(user_id, new_preferences)
        except Exception as e:
            print(f"❌ Error al actualizar preferencias: {e}")

    def _execute_main_loop(self, messages, query, memory_id, conversation_id, user_id: str):
        """
        Ejecuta el ciclo principal de conversación con el LLM.
        Usa herramientas modulares para diferentes funcionalidades.
        """

        # Get tool definitions from tool classes
        tool_metas = [
            self.extract_user_name_tool.get_tool_definition(),
            self.catalog_search_tool.get_tool_definition(),
            self.car_financial_tool.get_tool_definition(),
            self.kavak_info_search_tool.get_tool_definition()
        ]

        tool_choice = "auto"

        for step in range(5):
            kwargs = {
                "model": self.model,
                "messages": messages,
                "tool_choice": "auto",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            if tool_metas:
                kwargs["tools"] = tool_metas

            response = self.client.chat.completions.create(**kwargs)

            choice = response.choices[0]

            tool_calls = getattr(choice.message, "tool_calls", [])

            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.function.name == "extract_and_save_user_name":
                        args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        result = self.extract_user_name_tool.execute(args, user_id)

                        # Add assistant tool call to messages
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [tool_call],
                            "content": None
                        })

                        # Add tool response to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                    elif tool_call.function.name == "catalog_search":
                        args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        result = self.catalog_search_tool.execute(args, 5)

                        # Add assistant tool call to messages
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [tool_call],
                            "content": None
                        })

                        # Add tool response to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                    elif tool_call.function.name == "calculate_car_financing":
                        args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        result = self.car_financial_tool.execute(args, user_id)

                        # Add assistant tool call to messages
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [tool_call],
                            "content": None
                        })

                        # Add tool response to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                    elif tool_call.function.name == "kavak_info_search":
                        args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        result = self.kavak_info_search_tool.execute(args)

                        # Add assistant tool call to messages
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [tool_call],
                            "content": None
                        })

                        # Add tool response to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                # Second call after tool execution
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "tool_choice": "none"
                }

                if tool_metas:
                    kwargs["tools"] = tool_metas

                response = self.client.chat.completions.create(**kwargs)

                final_message = response.choices[0].message.content

                return final_message

            # If no tool_call, respond directly
            print("No se detectó tool_call, respondiendo directamente...\n")
            return choice.message.content

        # If we exceed steps without valid response
        raise RuntimeError("Max steps exceeded without reaching a final answer.")

