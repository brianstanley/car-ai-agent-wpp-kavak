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
        Summarize search results using a smaller model.

        Args:
            results: List of search results
            query: Original query

        Returns:
            str: Summarized response
        """
        if not results:
            return "No encontré información específica sobre tu consulta. ¿Podrías reformular tu pregunta?"

        if not self.client:
            # Fallback without summarization
            response = "Información encontrada:\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result.text}\n\n"
            return response

        # Prepare content for summarization
        content_parts = []
        for result in results:
            if hasattr(result, 'title') and result.title:
                content_parts.append(f"Título: {result.title}")
            content_parts.append(result.text)
            content_parts.append("---")

        content = "\n".join(content_parts)

        # Summarization prompt
        summary_prompt = f"""
        Eres un asistente experto de Kavak. El usuario preguntó: "{query}"

        Basándote en la siguiente información de Kavak, proporciona una respuesta clara, concisa y útil.
        La respuesta debe ser breve (máximo 200 palabras) y directa al punto.

        Información disponible:
        {content}

        Responde de manera natural y amigable, como si fueras un representante de Kavak ayudando al cliente.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using smaller model for summarization
                messages=[
                    {"role": "system", "content": "Eres un asistente experto de Kavak que proporciona información clara y concisa."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Error en summarización: {e}")
            # Fallback response
            return f"Encontré información sobre '{query}':\n\n" + "\n\n".join([result.text for result in results[:2]])

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

            print(f"🔍 Buscando información de Kavak: '{query}'")

            # Perform semantic search
            results = self.kavak_info_service.search_similar(query, limit=max_results)

            if not results:
                return f"No encontré información específica sobre '{query}'. ¿Podrías reformular tu pregunta o consultar sobre otro tema relacionado con Kavak?"

            # Summarize results
            summarized_response = self._summarize_results(results, query)

            print(f"✅ Encontrados {len(results)} resultados para '{query}'")
            return summarized_response

        except Exception as e:
            error_msg = f"❌ Error en búsqueda de información de Kavak: {e}"
            print(error_msg)
            return error_msg