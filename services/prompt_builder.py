#!/usr/bin/env python3
"""
Prompt Builder Service for constructing prompts with fluent interface.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from services.memory_service import MemoryService


class PromptBuilder:
    """Builder for constructing prompts with fluent interface."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the prompt builder.

        Args:
            memory_service: Memory service instance (injected)
        """
        self.system_prompt = ""
        self.memory_service = memory_service or MemoryService()
        self._reset()

    def _reset(self):
        """Reset builder state."""
        self.system_prompt = ""
        self.context_window = ""
        self.conversation_history = ""
        self.summaries = ""
        self.user_query = ""
        self.memory_id = None

    def add_system(self, persona, instruction: str) -> 'PromptBuilder':
        """
        Add system prompt component.

        Args:
            persona: The persona configuration
            instruction: The instruction for the agent

        Returns:
            PromptBuilder: Self for chaining
        """
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Build base prompt from persona and instruction
        prompt_base = ""
        if persona and instruction:
            persona_prompt = persona.generate_system_prompt_input()
            prompt_base = f"{persona_prompt}\n\n{instruction}"
        elif persona:
            prompt_base = persona.generate_system_prompt_input()
        else:
            prompt_base = instruction

        self.system_prompt = f"Fecha actual: {current_date}\n\n{prompt_base}"
        return self

    def build_messages_for_openai(self) -> List[Dict[str, str]]:
        """
        Build complete messages list for OpenAI API with proper role separation.

        Returns:
            List[Dict[str, str]]: Messages list for OpenAI API with clear roles
        """
        messages = []

        # 1. System message with persona and instruction
        system_content = self.system_prompt
        if self.context_window:
            system_content += f"\n\n{self.context_window}"
        if self.summaries:
            system_content += f"\n\n{self.summaries}"

        messages.append({"role": "system", "content": system_content})

        # 2. Add conversation history as separate messages with proper roles
        if self.conversation_history and self.memory_id:
            try:
                # Get the actual conversation history from memory service
                recent_messages = self.memory_service.get_last_n_messages(
                    UUID(self.memory_id), n=10
                )

                for msg in recent_messages:
                    role = msg['role']
                    content = msg['content']
                    # Map memory roles to OpenAI roles
                    if role == 'user':
                        messages.append({"role": "user", "content": content})
                    elif role == 'assistant':
                        messages.append({"role": "assistant", "content": content})
                    # Skip 'system' messages from history as they're already in system prompt

            except Exception as e:
                print(f"   ⚠️ Warning: Could not add conversation history to messages: {e}")

        # 3. Add current user query
        messages.append({"role": "user", "content": self.user_query})

        return messages