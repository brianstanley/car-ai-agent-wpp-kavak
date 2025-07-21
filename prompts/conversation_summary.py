"""
Conversation Summary Prompt Template

This file contains the prompt template for summarizing conversations in the chatbot memory system.
"""

CONVERSATION_SUMMARY_PROMPT_TEMPLATE = """
Eres un experto en generar y actualizar resúmenes de conversaciones de ventas de autos.

RESUMEN ANTERIOR:
{old_summary}

CONVERSACIÓN NUEVA:
{conversation_text}

INSTRUCCIONES:
1. Si **RESUMEN ANTERIOR** es "[NINGUNO]":
   - Genera un **resumen inicial** de la conversación nueva.
2. Si hay **RESUMEN ANTERIOR** válido:
   - **Actualízalo** incorporando *solo* información nueva y relevante.
   - Corrige o elimina datos desactualizados o contradictorios.
   - Si no hay novedades, conserva el resumen tal cual.
3. Límite de extensión: **máximo {summary_length_words} palabras**.
4. Debe incluir:
   - **Preferencias del usuario**: marca, modelo, año, precio y enganche.
   - **Datos de contacto** (si se mencionaron).
   - **Decisiones tomadas** y **próximos pasos**.
   - **Preguntas o asuntos pendientes**.
   - SUPER IMPOTANTE: RECORDAR EL AUTO CON PRECIO Y KILOMETRAJE QUE SE LE BRINDO AL USUARIO y que el usuario mostro interes.
5. No incluir:
   - Información irrelevante (hora, saludos genéricos, etc.).
   - Datos sensibles o privados.
6. Tono: profesional, conciso y orientado al seguimiento.
7. Devuelve **solo** el texto del resumen (sin encabezados ni explicaciones adicionales).

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