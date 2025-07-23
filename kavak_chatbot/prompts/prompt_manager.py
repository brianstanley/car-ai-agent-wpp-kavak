"""
Unified Prompt Manager for handling different agent prompts from text files.
"""

import os
from typing import Dict, Optional
from pathlib import Path


class PromptManager:
    """Manager for handling different agent prompts from text files."""

    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt text files. Defaults to the same directory as this file.
        """
        if prompts_dir is None:
            prompts_dir = os.path.dirname(os.path.abspath(__file__))

        self.prompts_dir = Path(prompts_dir)
        self._prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load all prompt text files from the prompts directory."""
        from pathlib import Path
        path_data = Path("data")
        path_prompts = path_data / "prompts"
        for txt_file in path_prompts.iterdir():
            prompt_name = txt_file.stem
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    self._prompts[prompt_name] = f.read().strip()
            except Exception as e:
                print(f"Warning: Could not load prompt from {txt_file}: {e}")

    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get a prompt by name.

        Args:
            prompt_name: Name of the prompt to retrieve (without .txt extension)

        Returns:
            Optional[str]: The prompt text or None if not found
        """
        return self._prompts.get(prompt_name)

    def get_formatted_prompt(self, prompt_name: str, **kwargs) -> Optional[str]:
        """
        Get a prompt by name and format it with the given parameters.

        Args:
            prompt_name: Name of the prompt to retrieve (without .txt extension)
            **kwargs: Parameters to format the prompt with

        Returns:
            Optional[str]: The formatted prompt text or None if not found
        """
        prompt = self.get_prompt(prompt_name)
        if prompt is None:
            return None

        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing parameter {e} for prompt {prompt_name}")
            return prompt

    def add_prompt(self, name: str, prompt: str):
        """
        Add a new prompt to the manager.

        Args:
            name: Name for the prompt
            prompt: The prompt text
        """
        self._prompts[name] = prompt

    def list_prompts(self) -> list:
        """
        List all available prompts.

        Returns:
            list: List of prompt names
        """
        return list(self._prompts.keys())

    def reload_prompts(self):
        """Reload all prompts from text files."""
        self._prompts.clear()
        self._load_prompts()

    # Convenience methods for specific prompts
    def get_car_sales_agent_prompt(self) -> str:
        """
        Get the car sales agent prompt.

        Returns:
            str: The car sales agent prompt
        """
        prompt = self.get_prompt('agent')
        if prompt is None:
            raise ValueError("Car sales agent prompt not found")
        return prompt

    def get_conversation_summary_prompt(self, old_summary: str = "[NINGUNO]", conversation_text: str = "", summary_length_words: int = 100) -> str:
        """
        Get the conversation summary prompt.

        Args:
            old_summary: Previous summary text or "[NINGUNO]" if none exists
            conversation_text: The new conversation text to summarize
            summary_length_words: Maximum number of words for the summary

        Returns:
            str: The conversation summary prompt
        """
        return self.get_formatted_prompt('conversation_summary',
                                       old_summary=old_summary,
                                       conversation_text=conversation_text,
                                       summary_length_words=summary_length_words)

    def get_conversation_summary_system_prompt(self) -> str:
        """
        Get the conversation summary system prompt.

        Returns:
            str: The conversation summary system prompt
        """
        return self.get_prompt('conversation_summary_system')

    def get_catalog_search_normalization_prompt(self, brand_list: str) -> str:
        """
        Get the catalog search normalization prompt.

        Args:
            brand_list: Comma-separated list of valid car brands

        Returns:
            str: The catalog search normalization prompt
        """
        return self.get_formatted_prompt('catalog_search', marcas_list=brand_list)

    def get_evaluator_prompt(self, user_query: str = "", agent_response: str = "", tools_invoked: str = "", expected: str = "", expected_tools: str = "") -> str:
        """
        Get the evaluator prompt.

        Args:
            user_query: The user's query
            agent_response: The agent's response
            tools_invoked: Tools invoked by the agent
            expected: Expected response
            expected_tools: Expected tools

        Returns:
            str: The evaluator prompt
        """
        return self.get_formatted_prompt('evaluator',
                                       user_query=user_query,
                                       agent_response=agent_response,
                                       tools_invoked=tools_invoked,
                                       expected=expected,
                                       expected_tools=expected_tools)

    def get_kavak_info_summary_prompt(self, query: str, content: str) -> str:
        """
        Get the kavak info summary prompt.

        Args:
            query: The user's query
            content: The content to summarize

        Returns:
            str: The kavak info summary prompt
        """
        return self.get_formatted_prompt('kavak_info_summary', query=query, content=content)

    def get_kavak_info_summary_system_prompt(self) -> str:
        """
        Get the kavak info summary system prompt.

        Returns:
            str: The kavak info summary system prompt
        """
        return self.get_prompt('kavak_info_summary_system')


# Global instance
prompt_manager = PromptManager()