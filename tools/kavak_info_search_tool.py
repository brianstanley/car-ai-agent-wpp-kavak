#!/usr/bin/env python3
"""
Tool for semantic search of Kavak information.
"""

from typing import Dict, Any, List, Optional
from openai import OpenAI
from enum import Enum

from services.kavak_info_service import KavakInfoService
from prompts.prompt_manager import prompt_manager
from services.llm_protocol import LLMClientProtocol


MAX_RESULTS_DEFAULT = 3
class KavakInfoSearchError(str, Enum):
    MISSING_QUERY = "Error: Se requiere una consulta para buscar información de Kavak."
    NOT_FOUND = "No encontré información específica sobre '{query}'. ¿Podrías reformular tu pregunta o consultar sobre otro tema relacionado con Kavak?"
    SUMMARIZATION = "Error en summarización: {error}"
    SEARCH = "Error en búsqueda de información de Kavak: {error}"

class KavakInfoSearchTool:
    def __init__(self, llm_client: Optional[LLMClientProtocol] = None):
        """
        Initialize the tool.

        Args:
            llm_client: LLM client for summarization
        """
        self.llm_client = llm_client
        self.kavak_info_service = KavakInfoService()

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for OpenAI API.

        Returns:
            Dict containing tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": "kavak_info_search",
                "description": (
                    "Busca información general de Kavak usando búsqueda semántica. "
                    "Puede responder preguntas sobre:\n"
                    "- Sucursales y ubicaciones de Kavak en México\n"
                    "- Servicios disponibles en cada sede (entrega, prueba de manejo, inspección, etc.)\n"
                    "- Documentación necesaria para financiar un auto\n"
                    "- Proceso de evaluación de vehículos\n"
                    "- Período de prueba\n"
                    "- Propuesta de valor general de Kavak\n\n"
                    "Devuelve información resumida y relevante."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Consulta sobre información de Kavak. "
                                "Ejemplos: '¿Dónde está la sede de Guadalajara?', "
                                "'¿Puedo hacer prueba de manejo en CDMX?', "
                                "'¿Qué horarios tiene la sucursal de Monterrey?', "
                                "'¿Qué documentacion requiero para financiar un auto?'."
                            )
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Número máximo de resultados a buscar (por defecto 3)",
                            "default": 4
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def _summarize_results(self, results: List[Any], query: str, model: str) -> str:
        """
        Summarize search results focusing on the client's query and the synthesized answer.

        Args:
            results: List of search results
            query: Original client query
            model: OpenAI model to use for summarization

        Returns:
            str: Focused summary with the key points and direct response
        """
        snippets = [res.text for res in results[:3]]
        content = "\n".join(snippets)
        summary_prompt = prompt_manager.get_kavak_info_summary_prompt(query, content)

        try:
            response = self.llm_client.chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_manager.get_kavak_info_summary_system_prompt()},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(KavakInfoSearchError.SUMMARIZATION.value.format(error=e))
            # Fallback: show query and up to two result snippets
            fallback = [res.text for res in results[:2]]
            items = "\n".join(f"- {text}" for text in fallback)
            return f"Consulta: \"{query}\"\nInformación encontrada:\n{items}"

    def execute(self, args: Dict[str, Any]) -> str:
        """
        Execute the Kavak info search tool.

        Args:
            args: Tool arguments containing 'query' and optional 'max_results'

        Returns:
            str: Summarized search results
        """
        try:
            query = args.get('query', '')
            max_results = args.get('max_results', MAX_RESULTS_DEFAULT)

            if not query:
                return KavakInfoSearchError.MISSING_QUERY.value

            print(f"TOOL CALL- Buscando información de Kavak: '{query}'")
            results = self.kavak_info_service.search_similar(query, limit=max_results) # use semantic search:)

            if not results:
                print(KavakInfoSearchError.NOT_FOUND.value.format(query=query))
                return KavakInfoSearchError.NOT_FOUND.value.format(query=query)

            summarized_response = self._summarize_results(results, query, model="gpt-4o-mini")
            return summarized_response

        except Exception as e:
            error_msg = KavakInfoSearchError.SEARCH.value.format(error=e)
            print(error_msg)
            return error_msg