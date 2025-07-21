#!/usr/bin/env python3
"""
Memory Agent service for running agents with memory and conversation context.
"""
import json
import os
import sys

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from openai import OpenAI
from dotenv import load_dotenv

from services.memory_service import MemoryService
from services.chat_service import ChatService
from services.session_service import SessionService
from services.prompt_builder import PromptBuilder
from services.user_service import UserService
from tools import ExtractUserNameTool, CatalogSearchTool, CarFinancialTool, KavakInfoSearchTool
from models.db.agent import AgentDB
from models.db.persona import PersonaDB
from models import Persona
from db.session import SessionLocal

# Load environment variables
load_dotenv()

# Configuration constants
class AgentConfig:
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_MAX_TOKENS = 1000
    DEFAULT_TEMPERATURE = 0.4
    MAX_CONVERSATION_STEPS = 5
    MAX_HISTORY_MESSAGES = 10
    USER_NAME_SECTION_WIDTH = 30
    PREFERENCES_SECTION_WIDTH = 50

class AgentService:
    """Memory Agent for running agents with memory and conversation context."""

    def __init__(
        self,
        persona,
        instruction,
        user,
        model: str = AgentConfig.DEFAULT_MODEL,
        memory_agent_i=None,
        *,
        openai_client: Optional[OpenAI] = None,
        memory_service: Optional[MemoryService] = None,
        chat_service: Optional[ChatService] = None,
        user_service: Optional[UserService] = None,
        session_service: Optional['SessionService'] = None,
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
            session_service: Session service instance (injected)
            prompt_builder: Prompt builder instance (injected)
        """
        self._validate_environment()
        self._initialize_dependencies(
            openai_client, memory_service, chat_service,
            user_service, session_service, prompt_builder
        )
        self._initialize_configuration(model, persona, instruction, memory_agent_i, user)
        self._initialize_tools()

    def _validate_environment(self) -> None:
        """Validate required environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables")
            sys.exit(1)

    def _initialize_dependencies(
        self,
        openai_client: Optional[OpenAI],
        memory_service: Optional[MemoryService],
        chat_service: Optional[ChatService],
        user_service: Optional[UserService],
        session_service: Optional['SessionService'],
        prompt_builder: Optional[PromptBuilder]
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai_client or OpenAI(api_key=api_key)
        self.memory_service = memory_service or MemoryService()
        self.chat_service = chat_service or ChatService()
        self.session_service = session_service or SessionService()
        self.user_service = user_service
        self.prompt_builder = prompt_builder

    def _initialize_configuration(
        self,
        model: str,
        persona,
        instruction,
        memory_agent_i,
        user
    ) -> None:
        self.model = model
        self.persona = persona
        self.instruction = instruction
        self.memory_agent_i = memory_agent_i
        self.user = user

    def _initialize_tools(self) -> None:
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
                instruction_val = str(agent.instruction) if agent.instruction is not None else None
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
            print(f"Chat Session ID: {chat_session_id}")

            # 1) Prepare memory and conversation IDs
            memory_id = self._validate_session_exists(chat_session_id)

            # 2) Build augmented query using PromptBuilder
            print("\nBuilding prompt...")
            messages = self._build_prompt_messages(query, memory_id)

            # LOG DEL PROMPT QUE SE VA A ENVIAR AL LLM
            print("\nPROMPT QUE SE ENVÍA AL LLM:")
            for i, msg in enumerate(messages):
                print(f"[{i}] {msg['role'].upper()}\n{msg['content']}\n{'-'*40}")

            # 5) Record user's query in memory
            self._record_user_query(query, chat_session_id)

            # 6) Get response from OpenAI
            print("\nGetting response from OpenAI...")
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

            # 8) Check if conversation should be summarized
            self._check_and_summarize_conversation(chat_session_id)

            return response or "No response received from agent"

        except Exception as e:
            error_msg = f"Error running MemAgent: {e}"
            print(error_msg)
            return error_msg

    def evaluate(self, user_query: str, chat_session_id: str):
        """
        Evalúa la respuesta del agente, devolviendo los elementos estructurados para el meta-agente evaluador.
        """
        memory_id = self._validate_session_exists(chat_session_id)
        messages = self._build_prompt_messages(user_query, memory_id)
        tool_metas = self._get_tool_definitions()
        # Solo hacemos una llamada, no el main loop
        response = self._make_openai_call(messages, tool_metas)
        choice = response.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", [])
        if tool_calls is None:
            tool_calls = []
        agent_response = choice.message.content if choice.message.content else ""
        # El specialized_prompt es el system message
        specialized_prompt = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        # El evaluation_trigger_prompt es el user_query
        evaluation_trigger_prompt = user_query
        # tools_invoked: lista de nombres de tools invocadas
        tools_invoked = []
        for tc in tool_calls:
            if hasattr(tc.function, 'name'):
                tools_invoked.append(tc.function.name)
        return {
            "specialized_prompt": specialized_prompt,
            "evaluation_trigger_prompt": evaluation_trigger_prompt,
            "agent_response": agent_response,
            "tools_invoked": tools_invoked
        }

    def _validate_session_exists(self, chat_session_id: str) -> str:
        """
        Validate that the session exists and return memory_id.

        Args:
            chat_session_id: The chat session ID to validate

        Returns:
            str: The memory_id (same as chat_session_id)

        Raises:
            ValueError: If session doesn't exist
        """
        try:
            # Validate UUID format
            session_uuid = UUID(chat_session_id)

            # Use injected session_service to validate session exists
            if self.session_service:
                session = self.session_service.get_session_by_id(session_uuid)
                if session:
                    print(f"   Session validated: {session.id}")
                    return chat_session_id  # Use as memory_id
                else:
                    raise ValueError(f"Session {chat_session_id} does not exist")
            else:
                # Fallback if session_service not available
                print(f"   SessionService not available, skipping validation")
                return chat_session_id

        except ValueError as e:
            print(f"   Session validation error: {e}")
            raise
        except Exception as e:
            print(f"   Error validating session: {e}")
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
            print(f"   Warning: Could not record user query: {e}")

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
            print(f"   Warning: Could not record assistant response: {e}")

    def _check_and_summarize_conversation(self, chat_session_id: str) -> None:
        """
        Check if conversation should be summarized and perform summarization if needed.

        Parameters:
            chat_session_id (str): The chat session ID.
        """
        try:
            session_uuid = UUID(chat_session_id)

            # Check if should summarize based on sliding window
            if self.memory_service.should_summarize_conversation(session_uuid):
                print(f"   Triggering conversation summarization for session: {chat_session_id}")

                # Perform summarization
                success = self.memory_service.summarize_conversation(session_uuid)

                if success:
                    print(f"   Conversation summarized successfully")
                else:
                    print(f"   Failed to summarize conversation")
            else:
                print(f"   No summarization needed for session: {chat_session_id}")

        except Exception as e:
            print(f"   Warning: Could not check/summarize conversation: {e}")

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

        # Step 1: Build system message
        system_message = self._build_system_message()
        messages.append(system_message)

        # Step 2: Add conversation history
        self._add_conversation_history(messages, memory_id)

        # Step 3: Add current user query
        messages.append({"role": "user", "content": query})

        # Step 4: Log final messages
        self._log_prompt_messages(messages)

        return messages

    def _build_system_message(self) -> Dict[str, str]:
        """Build the system message with persona, instruction, user name, and preferences."""
        print("   Step 1: Building system message...")

        # Build base system content
        system_content = self._build_base_system_content()

        # Add user name section
        system_content = self._add_user_name_to_system(system_content)

        # Add user preferences section
        system_content = self._add_user_preferences_to_system(system_content)

        return {"role": "system", "content": system_content}

    def _build_base_system_content(self) -> str:
        """Build the base system content with persona and instruction."""
        if self.prompt_builder:
            return self.prompt_builder.add_system(self.persona, self.instruction).system_prompt
        else:
            # Fallback if prompt_builder is not available
            return f"Eres un asistente experto de Kavak. {self.persona}\n\n{self.instruction}"

    def _add_user_name_to_system(self, system_content: str) -> str:
        """Add user name section to system content."""
        print("   Step 1.5: Adding user name...")
        user_name_section = self._build_user_name_section()
        if user_name_section:
            system_content += f"\n\n{user_name_section}"
        return system_content

    def _add_user_preferences_to_system(self, system_content: str) -> str:
        """Add user preferences section to system content."""
        print("   Step 1.6: Adding user preferences...")
        preferences_section = self._build_user_preferences_section()
        if preferences_section:
            system_content += f"\n\n{preferences_section}"
        return system_content

    def _add_conversation_history(self, messages: List[Dict[str, str]], memory_id: str) -> None:
        """Add conversation history to messages."""
        try:
            # Use optimized method that includes summary and only unsummarized messages
            conversation_messages = self.memory_service.get_session_messages_with_summary(
                UUID(memory_id)
            )

            history_count = 0
            summary_added = False

            for msg in conversation_messages:
                role = msg['role']
                content = msg['content']

                # Add summary message (system role)
                if role == 'system' and 'RESUMEN DE CONVERSACIÓN PASADA:' in content and not summary_added:
                    messages.append({"role": "system", "content": content})
                    summary_added = True
                    history_count += 1

                # Add user and assistant messages
                elif role in ['user', 'assistant']:
                    messages.append({"role": role, "content": content})
                    history_count += 1


        except Exception as e:
            print(f"   Warning: Could not add conversation history: {e}")

            # Fallback to original method if optimized method fails
            try:
                print(f"   Falling back to original method...")
                recent_messages = self.memory_service.get_last_n_messages(
                    UUID(memory_id),
                    n=AgentConfig.MAX_HISTORY_MESSAGES
                )
                history_count = 0

                for msg in recent_messages:
                    role = msg['role']
                    content = msg['content']
                    if role in ['user', 'assistant']:
                        messages.append({"role": role, "content": content})
                        history_count += 1


            except Exception as fallback_e:
                print(f"   Fallback also failed: {fallback_e}")

    def _log_prompt_messages(self, messages: List[Dict[str, str]]) -> None:
        """Log the final prompt messages for debugging."""
        for i, msg in enumerate(messages):
            print(f"  [{i}] {msg['role'].upper()}: {msg['content'][:50]}...")

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
                "max_tokens": AgentConfig.DEFAULT_MAX_TOKENS,
                "temperature": AgentConfig.DEFAULT_TEMPERATURE
            }

            if tools:
                kwargs["tools"] = tools

            completion = self.client.chat.completions.create(**kwargs)

            response = completion.choices[0].message.content
            if response is None:
                return "No response received from OpenAI"

            return response

        except Exception as e:
            return f"Error getting response from OpenAI: {e}"

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
        preferences_text += "=" * AgentConfig.PREFERENCES_SECTION_WIDTH + "\n"

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

        preferences_text += "=" * AgentConfig.PREFERENCES_SECTION_WIDTH + "\n"

        print(f"   Added user preferences to system message")
        return preferences_text

    def _build_user_name_section(self) -> str:
        """
        Build a formatted string containing the user's name for inclusion in the system message.

        Returns:
            str: Formatted user name section or empty string if no name
        """
        if not self.user:
            return ""

        # Get user name from different possible sources
        user_name = None

        # Try to get name from user object
        if hasattr(self.user, 'name') and self.user.name:
            user_name = self.user.name
        # Try to get name from preferences
        elif hasattr(self.user, 'preferences') and self.user.preferences:
            if isinstance(self.user.preferences, dict) and self.user.preferences.get('name'):
                user_name = self.user.preferences['name']

        if not user_name:
            return ""

        # Build user name section
        user_name_text = "INFORMACIÓN DEL USUARIO:\n"
        user_name_text += "=" * AgentConfig.USER_NAME_SECTION_WIDTH + "\n"
        user_name_text += f"Nombre: {user_name}\n"
        user_name_text += "=" * AgentConfig.USER_NAME_SECTION_WIDTH + "\n"

        print(f"   Added user name '{user_name}' to system message")
        return user_name_text

    def _merge_preferences(self, user_id, new_preferences: dict):
        """
        Merges new preferences into the user's existing preferences in the database.
        Parameters:
            user_id (str): The ID of the user whose preferences are being updated.
            new_preferences (dict): The new preferences to merge into the user's existing preferences.
        """
        print(f"Updating preferences for user {user_id}...")
        try:
            if self.user_service:
                self.user_service.update_preferences(user_id, new_preferences)
        except Exception as e:
            print(f"Error al actualizar preferencias: {e}")

    def _execute_main_loop(self, messages, query, memory_id, conversation_id, user_id: str):
        """
        Ejecuta el ciclo principal de conversación con el LLM.
        Usa herramientas modulares para diferentes funcionalidades.
        """
        tool_metas = self._get_tool_definitions()

        for step in range(AgentConfig.MAX_CONVERSATION_STEPS):
            response = self._make_openai_call(messages, tool_metas)
            choice = response.choices[0]
            tool_calls = getattr(choice.message, "tool_calls", [])

            if tool_calls:
                self._process_tool_calls(tool_calls, messages, user_id)
                return self._get_final_response(messages, tool_metas)
            else:
                print("No se detectó tool_call, respondiendo directamente...\n")
                return choice.message.content

        raise RuntimeError("Max steps exceeded without reaching a final answer.")

    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions from tool classes."""
        return [
            self.extract_user_name_tool.get_tool_definition(),
            self.catalog_search_tool.get_tool_definition(),
            self.car_financial_tool.get_tool_definition(),
            self.kavak_info_search_tool.get_tool_definition()
        ]

    def _make_openai_call(self, messages: List[Dict], tool_metas: List[Dict]) -> Any:
        """Make OpenAI API call with tools."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "tool_choice": "auto",
            "max_tokens": AgentConfig.DEFAULT_MAX_TOKENS,
            "temperature": AgentConfig.DEFAULT_TEMPERATURE
        }

        if tool_metas:
            kwargs["tools"] = tool_metas

        return self.client.chat.completions.create(**kwargs)

    def _process_tool_calls(self, tool_calls: List, messages: List[Dict], user_id: str) -> None:
        """Process tool calls and add results to messages."""
        tool_handlers = {
            "extract_and_save_user_name": self._handle_extract_user_name,
            "catalog_search": self._handle_catalog_search,
            "calculate_car_financing": self._handle_car_financing,
            "kavak_info_search": self._handle_kavak_info_search
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name in tool_handlers:
                tool_handlers[function_name](tool_call, messages, user_id)

    def _handle_extract_user_name(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        """Handle extract user name tool call."""
        args = json.loads(tool_call.function.arguments)
        result = self.extract_user_name_tool.execute(args, user_id)
        self._add_tool_response(tool_call, result, messages)

    def _handle_catalog_search(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        """Handle catalog search tool call."""
        args = json.loads(tool_call.function.arguments)
        result = self.catalog_search_tool.execute(args, 5)
        self._add_tool_response(tool_call, result, messages)

    def _handle_car_financing(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        """Handle car financing tool call."""
        args = json.loads(tool_call.function.arguments)
        result = self.car_financial_tool.execute(args, user_id)
        self._add_tool_response(tool_call, result, messages)

    def _handle_kavak_info_search(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        """Handle kavak info search tool call."""
        args = json.loads(tool_call.function.arguments)
        result = self.kavak_info_search_tool.execute(args)
        self._add_tool_response(tool_call, result, messages)

    def _add_tool_response(self, tool_call: Any, result: str, messages: List[Dict]) -> None:
        """Add tool call and response to messages."""
        messages.append({
            "role": "assistant",
            "tool_calls": [tool_call],
            "content": None
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    def _get_final_response(self, messages: List[Dict], tool_metas: List[Dict]) -> str:
        """Get final response after tool execution."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "tool_choice": "none"
        }

        if tool_metas:
            kwargs["tools"] = tool_metas

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

