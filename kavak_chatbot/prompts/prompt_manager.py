"""
Unified Prompt Manager for handling different agent prompts from text files.
"""

import logging
import os
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            prompts_dir = os.path.dirname(os.path.abspath(__file__))

        self.prompts_dir = Path(prompts_dir)
        self._prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self):
        from pathlib import Path
        path_data = Path("data")
        path_prompts = path_data / "prompts"
        for txt_file in path_prompts.iterdir():
            prompt_name = txt_file.stem
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    self._prompts[prompt_name] = f.read().strip()
            except Exception as e:
                logger.warning(f"Could not load prompt from {txt_file}: {e}")

    def get_prompt(self, prompt_name: str) -> Optional[str]:

        return self._prompts.get(prompt_name)

    def get_formatted_prompt(self, prompt_name: str, **kwargs) -> Optional[str]:

        prompt = self.get_prompt(prompt_name)
        if prompt is None:
            return None

        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing parameter {e} for prompt {prompt_name}")
            return prompt

    def add_prompt(self, name: str, prompt: str):
        self._prompts[name] = prompt

    def list_prompts(self) -> list:
        return list(self._prompts.keys())

    def reload_prompts(self):
        self._prompts.clear()
        self._load_prompts()

    # Convenience methods for specific prompts
    def get_car_sales_agent_prompt(self) -> str:
        prompt = self.get_prompt('agent')
        if prompt is None:
            raise ValueError("Car sales agent prompt not found")
        return prompt

    def get_conversation_summary_prompt(self, old_summary: str = "[NINGUNO]", conversation_text: str = "", summary_length_words: int = 100) -> str:
        return self.get_formatted_prompt('conversation_summary',
                                       old_summary=old_summary,
                                       conversation_text=conversation_text,
                                       summary_length_words=summary_length_words)

    def get_conversation_summary_system_prompt(self) -> str:
        return self.get_prompt('conversation_summary_system')

    def get_catalog_search_normalization_prompt(self, brand_list: str) -> str:
        return self.get_formatted_prompt('catalog_search', marcas_list=brand_list)

    def get_evaluator_prompt(self, user_query: str = "", agent_response: str = "", tools_invoked: str = "", expected: str = "", expected_tools: str = "") -> str:
        return self.get_formatted_prompt('evaluator',
                                       user_query=user_query,
                                       agent_response=agent_response,
                                       tools_invoked=tools_invoked,
                                       expected=expected,
                                       expected_tools=expected_tools)

    def get_kavak_info_summary_prompt(self, query: str, content: str) -> str:
        return self.get_formatted_prompt('kavak_info_summary', query=query, content=content)

    def get_kavak_info_summary_system_prompt(self) -> str:
        return self.get_prompt('kavak_info_summary_system')


# Global instance
prompt_manager = PromptManager()