"""
Agent service for managing conversation with LLM.
"""

import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

from kavak_chatbot.services.memory_service import MemoryService
from kavak_chatbot.services.chat_service import ChatService
from kavak_chatbot.services.session_service import SessionService
from kavak_chatbot.services.prompt_builder import PromptBuilder
from kavak_chatbot.services.user_service import UserService
from kavak_chatbot.models.db.agent import AgentDB
from kavak_chatbot.models.db.persona import PersonaDB
from kavak_chatbot.models import Persona
from db.session import SessionLocal
from kavak_chatbot.services.llm_protocol import LLMClientProtocol


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
        llm_client: LLMClientProtocol = None,
        memory_service: Optional[MemoryService] = None,
        chat_service: Optional[ChatService] = None,
        user_service: Optional[UserService] = None,
        session_service: Optional['SessionService'] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        self._validate_environment()
        self._initialize_dependencies(
            llm_client, memory_service, chat_service,
            user_service, session_service, prompt_builder
        )
        self._initialize_configuration(model, persona, instruction, memory_agent_i, user)
        self._initialize_tools()

    def _validate_environment(self) -> None:
        """Validate required environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            sys.exit(1)

    def _initialize_dependencies(
        self,
        llm_client: LLMClientProtocol,
        memory_service: Optional[MemoryService],
        chat_service: Optional[ChatService],
        user_service: Optional[UserService],
        session_service: Optional['SessionService'],
        prompt_builder: Optional[PromptBuilder]
    ) -> None:
        self.client = llm_client
        self.memory_service = memory_service or MemoryService(llm_client=self.client)
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
        from kavak_chatbot.tools import ExtractUserNameTool, CatalogSearchTool, CarFinancialTool, KavakInfoSearchTool
        self.extract_user_name_tool = ExtractUserNameTool(user_service=self.user_service)
        self.catalog_search_tool = CatalogSearchTool(llm_client=self.client)
        self.car_financial_tool = CarFinancialTool()
        self.kavak_info_search_tool = KavakInfoSearchTool(llm_client=self.client)

    @staticmethod
    def fetch_memory_agent_data(agent_id: str) -> Tuple[Optional[Persona], Optional[str]]:
        try:
            with SessionLocal() as session:
                # Fetch agent with persona relationship
                agent = session.query(AgentDB).filter(AgentDB.id == UUID(agent_id)).first()

                if not agent:
                    logger.warning(f"Agent with ID {agent_id} not found")
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
            logger.error(f"Error fetching memory agent data: {e}")
            return None, None

    def run(self, query: str, chat_session_id: str) -> str:
        try:
            # print(f"Chat Session ID: {chat_session_id}")
            memory_id = self._validate_session_exists(chat_session_id)

            messages = self._build_prompt_messages(query, memory_id)

            # Record user's query in memory
            self._record_user_query(query, chat_session_id)

            response = self._execute_main_loop(
                messages=messages,
                query=query,
                memory_id=memory_id,
                conversation_id=chat_session_id,
                user_id=self.user.id
            )

            # Record assistant response in memory
            if response:
                self._record_assistant_response(response, chat_session_id)

            # Check if conversation should be summarized
            self._check_and_summarize_conversation(chat_session_id)

            return response or "No response received from agent"

        except Exception as e:
            error_msg = f"Error running MemAgent: {e}"
            logger.error(error_msg)
            return error_msg

    def evaluate(self, user_query: str, chat_session_id: str):
        """
        evaluate the agent's response to a user query.
        """
        memory_id = self._validate_session_exists(chat_session_id)
        messages = self._build_prompt_messages(user_query, memory_id)
        tool_metas = self._get_tool_definitions()

        response = self._make_openai_call(messages, tool_metas)
        choice = response.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", [])
        if tool_calls is None:
            tool_calls = []
        agent_response = choice.message.content if choice.message.content else ""
        specialized_prompt = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        evaluation_trigger_prompt = user_query
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
        try:
            # Validate UUID format
            session_uuid = UUID(chat_session_id)

            # Use injected session_service to validate session exists
            if self.session_service:
                session = self.session_service.get_session_by_id(session_uuid)
                if session:
                    # print(f"   Session validated: {session.id}")
                    return chat_session_id  # Use as memory_id
                else:
                    raise ValueError(f"Session {chat_session_id} does not exist")
            else:
                # Fallback if session_service not available
                logger.debug("SessionService not available, skipping validation")
                return chat_session_id

        except ValueError as e:
            logger.error(f"Session validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            raise

    def _record_user_query(self, query: str, chat_session_id: str) -> None:
        try:
            self.memory_service.store_message(UUID(chat_session_id), "user", query)
        except Exception as e:
            logger.warning(f"Could not record user query: {e}")

    def _record_assistant_response(self, response: str, chat_session_id: str) -> None:
        try:
            self.memory_service.store_message(UUID(chat_session_id), "assistant", response)
        except Exception as e:
            logger.warning(f"Could not record assistant response: {e}")

    def _check_and_summarize_conversation(self, chat_session_id: str) -> None:

        try:
            session_uuid = UUID(chat_session_id)

            # Check if should summarize based on sliding window
            if self.memory_service.should_summarize_conversation(session_uuid):
                logger.info(f"Triggering conversation summarization for session: {chat_session_id}")
                success = self.memory_service.summarize_conversation(session_uuid)

                if success:
                    logger.debug("Conversation summarized successfully")
                else:
                    logger.warning("Failed to summarize conversation")
            else:
                logger.debug(f"No summarization needed for session: {chat_session_id}")

        except Exception as e:
            logger.warning(f"Could not check/summarize conversation: {e}")

    def _build_prompt_messages(self, query: str, memory_id: str) -> List[Dict[str, str]]:
        messages = []

        # Step 1: Build system message
        system_message = self._build_system_message()
        messages.append(system_message)

        # Step 2: Add conversation history
        self._add_conversation_history(messages, memory_id)

        # Step 3: Add current user query
        messages.append({"role": "user", "content": query})


        return messages

    def _build_system_message(self) -> Dict[str, str]:
        """Build the system message with persona, instruction, user name, and preferences."""
        system_content = self._build_base_system_content()
        system_content = self._add_user_name_to_system(system_content)
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
        user_name_section = self._build_user_name_section()
        if user_name_section:
            system_content += f"\n\n{user_name_section}"
        return system_content

    def _add_user_preferences_to_system(self, system_content: str) -> str:
        preferences_section = self._build_user_preferences_section()
        if preferences_section:
            system_content += f"\n\n{preferences_section}"
        return system_content

    def _add_conversation_history(self, messages: List[Dict[str, str]], memory_id: str) -> None:
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
            try:
                logger.debug("Falling back to original method...")
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
                logger.warning(f"Fallback also failed: {fallback_e}")


    def _get_openai_response(self, messages: List[Any], tools: Optional[List[Dict]] = None) -> str:
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": AgentConfig.DEFAULT_MAX_TOKENS,
                "temperature": AgentConfig.DEFAULT_TEMPERATURE
            }

            if tools:
                kwargs["tools"] = tools

            completion = self.client.chat_completion(**kwargs)

            response = completion.choices[0].message.content
            if response is None:
                return "No response received from LLM"

            return response

        except Exception as e:
            return f"Error getting response from LLM: {e}"

    def _build_user_preferences_section(self) -> str:
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

        logger.debug("Added user preferences to system message")
        return preferences_text

    def _build_user_name_section(self) -> str:
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

        logger.debug(f"Added user name '{user_name}' to system message")
        return user_name_text

    def _merge_preferences(self, user_id, new_preferences: dict):
        logger.info(f"Updating preferences for user {user_id}...")
        try:
            if self.user_service:
                self.user_service.update_preferences(user_id, new_preferences)
        except Exception as e:
            logger.error(f"Error al actualizar preferencias: {e}")

    def _execute_main_loop(self, messages, query, memory_id, conversation_id, user_id: str):
        """
        Main loop for running the agent with conversation context and tool calls.
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
                return choice.message.content

        raise RuntimeError("Max steps exceeded without reaching a final answer.")

    def _get_tool_definitions(self) -> List[Dict]:
        return [
            self.extract_user_name_tool.get_tool_definition(),
            self.catalog_search_tool.get_tool_definition(),
            self.car_financial_tool.get_tool_definition(),
            self.kavak_info_search_tool.get_tool_definition()
        ]

    def _make_openai_call(self, messages: List[Dict], tool_metas: List[Dict]) -> Any:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "tool_choice": "auto",
            "max_tokens": AgentConfig.DEFAULT_MAX_TOKENS,
            "temperature": AgentConfig.DEFAULT_TEMPERATURE
        }

        if tool_metas:
            kwargs["tools"] = tool_metas

        return self.client.chat_completion(**kwargs)

    def _process_tool_calls(self, tool_calls: List, messages: List[Dict], user_id: str) -> None:
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
        args = json.loads(tool_call.function.arguments)
        result = self.extract_user_name_tool.execute(args, user_id)
        self._add_tool_response(tool_call, result, messages)

    def _handle_catalog_search(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        args = json.loads(tool_call.function.arguments)
        result = self.catalog_search_tool.execute(args, 5)
        self._add_tool_response(tool_call, result, messages)

    def _handle_car_financing(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
        args = json.loads(tool_call.function.arguments)
        result = self.car_financial_tool.execute(args, user_id)
        self._add_tool_response(tool_call, result, messages)

    def _handle_kavak_info_search(self, tool_call: Any, messages: List[Dict], user_id: str) -> None:
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

        response = self.client.chat_completion(**kwargs)
        return response.choices[0].message.content

