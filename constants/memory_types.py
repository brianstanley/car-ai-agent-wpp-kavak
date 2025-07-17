from enum import Enum

class MemoryType(Enum):
    """Types of memory stores available in the system."""
    CONVERSATION_MEMORY = "conversation_memory"
    SUMMARIES = "summaries"

    @classmethod
    def get_description(cls, memory_type) -> str:
        """Get description for a memory type."""
        descriptions = {
            cls.CONVERSATION_MEMORY: "Stores conversation history between agent and user",
            cls.SUMMARIES: "Stores compressed summaries of past conversations"
        }
        return descriptions.get(memory_type, "Unknown memory type")

    @classmethod
    def get_usage(cls, memory_type) -> str:
        """Get usage instructions for a memory type."""
        usages = {
            cls.CONVERSATION_MEMORY: "Use for continuity and avoiding repetition",
            cls.SUMMARIES: "Use for broader context and personalization"
        }
        return usages.get(memory_type, "No usage instructions available")