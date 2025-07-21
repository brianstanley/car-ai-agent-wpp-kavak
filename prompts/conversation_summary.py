"""
Conversation Summary Prompt Template

This file contains the prompt template for summarizing conversations in the chatbot memory system.
"""

CONVERSATION_SUMMARY_PROMPT_TEMPLATE = """
Eres un especialista en resumir conversaciones de ventas de autos con memoria incremental.

RESUMEN ANTERIOR (puede estar vacío si es la primera vez):
{old_summary}

CONVERSACIÓN NUEVA:
{conversation_text}

INSTRUCCIONES:
1. Si **RESUMEN ANTERIOR** está vacío ("[NINGUNO]"), genera un **resumen inicial** de la conversación nueva.
2. Si **hay RESUMEN ANTERIOR**, **actualízalo**:
   - Añade **solo** información nueva y relevante.
   - Corrige o elimina datos que ya no sean válidos o que contradigan el resumen previo.
   - Si no hay cambios, conserva el contenido original.
3. Limita el resumen a **máximo {summary_length_words} palabras**.
4. Enfócate en:
   - Preferencias del usuario (marca, modelo, año, precio)
   - Información de contacto
   - Decisiones tomadas
   - Preguntas pendientes
   - Próximos pasos
5. Mantén un tono profesional, conciso y orientado al seguimiento.
6. Devuelve **solo** el texto del resumen actualizado, sin encabezados ni explicaciones adicionales.
7. No guardes informacion sensible o personal del usuario.
8. No guardes informacion no relevante como que el usuario pregunto que dia es hoy o que hora es.

RESUMEN:
"""

CONVERSATION_SUMMARY_SYSTEM_PROMPT = "Eres un especialista en resumir conversaciones de ventas de autos de manera concisa y útil."

KAVAK_INFO_SUMMARY_SYSTEM_PROMPT = (
    "Eres un experto en resumir contenido complejo, capaz de identificar y mantener los aspectos más importantes. "
    "Tu objetivo es ofrecer un resumen claro, conciso y preciso que incluya la pregunta del cliente y los puntos clave sin perder contexto."
)


def get_conversation_summary_prompt(
    old_summary: str = "[NINGUNO]",
    conversation_text: str = "",
    summary_length_words: int = 100
) -> str:
    """
    Get the conversation summary prompt template with the given parameters.

    Args:
        old_summary: Previous summary text or "[NINGUNO]" if none exists
        conversation_text: The new conversation text to summarize
        summary_length_words: Maximum number of words for the summary

    Returns:
        str: The formatted prompt for conversation summarization
    """
    return CONVERSATION_SUMMARY_PROMPT_TEMPLATE.format(
        old_summary=old_summary,
        conversation_text=conversation_text,
        summary_length_words=summary_length_words
    )


def get_conversation_summary_system_prompt() -> str:
    """
    Get the system prompt for conversation summarization.

    Returns:
        str: The system prompt for conversation summarization
    """
    return CONVERSATION_SUMMARY_SYSTEM_PROMPT


def get_kavak_info_summary_prompt(query: str, content: str) -> str:
    return f'''
        La consulta del cliente es:
        "{query}"
        
        Información relevante encontrada (resumida):
        {content}
        
    '''


def get_kavak_info_summary_system_prompt() -> str:
    return KAVAK_INFO_SUMMARY_SYSTEM_PROMPT