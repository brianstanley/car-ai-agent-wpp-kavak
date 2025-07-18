from enum import Enum

class MemoryType(Enum):
    """Tipos de memoria disponibles en el sistema."""
    CONVERSATION_MEMORY = "conversation_memory"
    SUMMARIES = "summaries"

    @classmethod
    def get_description(cls, memory_type) -> str:
        """Descripción de cada tipo de memoria."""
        descriptions = {
            cls.CONVERSATION_MEMORY: "Memoria de conversación: guarda el historial reciente entre el agente y el usuario.",
            cls.SUMMARIES: "Resúmenes: contiene un resumen comprimido de conversaciones pasadas y preferencias del usuario."
        }
        return descriptions.get(memory_type, "Tipo de memoria desconocido.")

    @classmethod
    def get_usage(cls, memory_type) -> str:
        """Instrucciones de uso para cada tipo de memoria."""
        usages = {
            cls.CONVERSATION_MEMORY: "Úsala para mantener la continuidad y evitar repeticiones innecesarias.",
            cls.SUMMARIES: "Úsala para entender mejor al usuario y personalizar la conversación según su historial."
        }
        return usages.get(memory_type, "No hay instrucciones de uso disponibles.")
