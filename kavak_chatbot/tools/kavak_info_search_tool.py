from typing import Dict, Any, List, Optional
from enum import Enum
import logging

from kavak_chatbot.services.kavak_info_service import KavakInfoService
from kavak_chatbot.prompts.prompt_manager import prompt_manager
from kavak_chatbot.services.llm_protocol import LLMClientProtocol

logger = logging.getLogger(__name__)


MAX_RESULTS_DEFAULT = 3
class KavakInfoSearchError(str, Enum):
    MISSING_QUERY = "Error: Se requiere una consulta para buscar información de Kavak."
    NOT_FOUND = "No encontré información específica sobre '{query}'. ¿Podrías reformular tu pregunta o consultar sobre otro tema relacionado con Kavak?"
    SUMMARIZATION = "Error en summarización: {error}"
    SEARCH = "Error en búsqueda de información de Kavak: {error}"

class KavakInfoSearchTool:
    def __init__(self, llm_client: Optional[LLMClientProtocol] = None):
        self.llm_client = llm_client
        self.kavak_info_service = KavakInfoService()

    def get_tool_definition(self) -> Dict[str, Any]:
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
            logger.error(KavakInfoSearchError.SUMMARIZATION.value.format(error=e))
            # Fallback: show query and up to two result snippets
            fallback = [res.text for res in results[:2]]
            items = "\n".join(f"- {text}" for text in fallback)
            return f"Consulta: \"{query}\"\nInformación encontrada:\n{items}"

    def execute(self, args: Dict[str, Any]) -> str:
        try:
            query = args.get('query', '')
            max_results = args.get('max_results', MAX_RESULTS_DEFAULT)

            if not query:
                return KavakInfoSearchError.MISSING_QUERY.value

            logger.info(f"TOOL CALL- Buscando información de Kavak: '{query}'")
            results = self.kavak_info_service.search_similar(query, limit=max_results) # use semantic search:)

            if not results:
                logger.warning(KavakInfoSearchError.NOT_FOUND.value.format(query=query))
                return KavakInfoSearchError.NOT_FOUND.value.format(query=query)

            summarized_response = self._summarize_results(results, query, model="gpt-4o-mini")
            return summarized_response

        except Exception as e:
            error_msg = KavakInfoSearchError.SEARCH.value.format(error=e)
            logger.error(error_msg)
            return error_msg