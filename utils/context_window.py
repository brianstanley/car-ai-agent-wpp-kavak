from typing import List

from constants import MemoryType


class ContextWindow:
    @staticmethod
    def get_prompt_from_memory_types(memory_types: List[MemoryType]):
        prompt = (
            "Eres un agente inteligente con un sistema de memoria avanzado. Usa toda tu memoria para:\n"
            "- Mantener la continuidad de la conversación sin repetir saludos ni datos que ya conoces.\n"
            "- Personalizar las respuestas con base en el historial y preferencias previas.\n"
            "- Ofrecer respuestas precisas, útiles y naturales.\n\n"
            "Tipos de memoria disponibles:"
        )
        for memory_type in memory_types:
            prompt += ContextWindow._generate_prompt_for_memory_type(memory_type)

        return prompt

    @staticmethod
    def _generate_prompt_for_memory_type(memory_type: MemoryType):
        # Define memory type prompts in a dictionary for better maintainability
        memory_prompts = {
            MemoryType.CONVERSATION_MEMORY: {
                "description": MemoryType.get_description(MemoryType.CONVERSATION_MEMORY),
                "usage": MemoryType.get_usage(MemoryType.CONVERSATION_MEMORY)
            },
            MemoryType.SUMMARIES: {
                "description": MemoryType.get_description(MemoryType.SUMMARIES),
                "usage": MemoryType.get_usage(MemoryType.SUMMARIES)
            }
        }

        # Get the prompt configuration for this memory type
        prompt_config = memory_prompts.get(memory_type)

        if prompt_config:
            prompt = f"\n\nMemory Type: {memory_type.value}\n"
            prompt += f"Memory Type Description: {prompt_config['description']}\n"
            prompt += f"Memory Type Usage: {prompt_config['usage']}\n"
            return prompt
        else:
            # Handle unknown memory types gracefully
            return f"\n\nMemory Type: {memory_type.value}\n"

# Can take in an array of memory stores and then return a prompt that informs the agent on how to manage the context window