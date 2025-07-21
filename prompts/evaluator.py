"""
Evaluator Prompt Template

This file contains the prompt template for evaluating agent responses and tool usage in Kavak's chatbot system.
"""

EVALUATOR_PROMPT_TEMPLATE = """
Eres un evaluador automático. Tu tarea es analizar la interacción entre un usuario y un agente conversacional de ventas de autos.

Te doy:
- Consulta del usuario: {user_query}
- Respuesta del agente: {agent_response}
- Tools invocadas por el agente: {tools_invoked}
- Respuesta esperada: {expected}
- Tools esperadas: {expected_tools}

Evalúa lo siguiente:
1. ¿Las tools invocadas coinciden con las esperadas? Responde  true o false.
2. ¿La respuesta del agente es coherente y cumple con lo esperado? true o false.
3. Si se indica que se uso la tool esperada es suficiente para el test. No se requiere analziar la respuesta del agente en este momento.
Devuelve tu análisis en formato JSON con los campos: tools_match, tools_comments, response_match, response_comments.
4. Si no hay expected_tools, entonces tools_match = true
"""

def get_evaluator_prompt() -> str:
    """
    Get the evaluator prompt template.

    Returns:
        str: The formatted prompt for the evaluator agent
    """
    return EVALUATOR_PROMPT_TEMPLATE.strip()