"""
Prompt Manager for handling different agent prompts.
"""

from typing import Dict, Optional
from .car_sales_agent import get_car_sales_agent_prompt
from .conversation_summary import get_conversation_summary_prompt, get_conversation_summary_system_prompt


class PromptManager:
    """Manager for handling different agent prompts."""
    
    def __init__(self):
        self._prompts: Dict[str, str] = {}
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Load default prompts."""
        self._prompts['car_sales_agent'] = get_car_sales_agent_prompt()
        self._prompts['conversation_summary'] = get_conversation_summary_prompt()
        self._prompts['conversation_summary_system'] = get_conversation_summary_system_prompt()
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get a prompt by name.
        
        Args:
            prompt_name: Name of the prompt to retrieve
            
        Returns:
            Optional[str]: The prompt text or None if not found
        """
        return self._prompts.get(prompt_name)
    
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
    
    def get_car_sales_agent_prompt(self) -> str:
        """
        Get the car sales agent prompt.
        
        Returns:
            str: The car sales agent prompt
        """
        prompt = self.get_prompt('car_sales_agent')
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
        return get_conversation_summary_prompt(old_summary, conversation_text, summary_length_words)

    def get_conversation_summary_system_prompt(self) -> str:
        """
        Get the conversation summary system prompt.
        
        Returns:
            str: The conversation summary system prompt
        """
        return get_conversation_summary_system_prompt()


# Global instance
prompt_manager = PromptManager() 