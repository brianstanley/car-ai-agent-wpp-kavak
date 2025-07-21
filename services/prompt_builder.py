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
