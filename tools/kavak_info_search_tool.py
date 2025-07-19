#!/usr/bin/env python3
"""
Tool for semantic search of Kavak information.
"""

import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

from services.kavak_info_service import KavakInfoService


class KavakInfoSearchTool:
    """Tool for searching Kavak information using semantic search."""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Initialize the tool.

        Args:
            openai_client: OpenAI client for summarization
        """
        self.client = openai_client
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
                    "- Modalidades de atención (presencial, online, híbrido)\n"
                    "- Horarios de atención de cada sede\n"
                    "- Documentación necesaria para comprar un auto\n"
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
                                "'¿Qué servicios hay en Mérida?', '¿Qué necesito para comprar un auto?'."
                            )
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Número máximo de resultados a buscar (por defecto 3)",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def _summarize_results(self, results: List[Any], query: str) -> str:
        """
        Summarize search results focusing on the client's query and the synthesized answer.

        Args:
            results: List of search results
            query: Original client query

        Returns:
            str: Focused summary with the key points and direct response
        """
        snippets = [res.text for res in results[:3]]
        content = "\n".join(snippets)

        # Build a prompt that asks only for key points and a direct response
        summary_prompt = f"""
            La consulta del cliente es:
            "{query}"
            
            Información relevante encontrada (resumida):
            {content}
            
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "Eres un **experto en resumir** contenido complejo, capaz de identificar y mantener los aspectos más importantes. "
                        "Tu objetivo es ofrecer un resumen claro, conciso y preciso que incluya la pregunta del cliente y los puntos clave sin perder contexto." )},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Error en summarización: {e}")
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
            max_results = args.get('max_results', 3)

            if not query:
                return "❌ Error: Se requiere una consulta para buscar información de Kavak."

            print(f"🔍 TOOL CALL- Buscando información de Kavak: '{query}'")

            # Perform semantic search
            results = self.kavak_info_service.search_similar(query, limit=max_results)

            if not results:
                print(f"❌ No encontré información específica sobre '{query}'.")
                return f"No encontré información específica sobre '{query}'. ¿Podrías reformular tu pregunta o consultar sobre otro tema relacionado con Kavak?"

            summarized_response = self._summarize_results(results, query)
            print(f"✅ Encontrados {len(results)} resultados para '{query}'")
            print(f"🔍 luego de sumarizar los resultados: {summarized_response}")
            return summarized_response

        except Exception as e:
            error_msg = f"❌ Error en búsqueda de información de Kavak: {e}"
            print(error_msg)
            return error_msg