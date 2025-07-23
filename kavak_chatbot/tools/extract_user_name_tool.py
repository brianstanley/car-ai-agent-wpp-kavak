"""
Tool for extracting and saving user names.
"""

from typing import Dict, Any, Optional
from kavak_chatbot.services.user_service import UserService


class ExtractUserNameTool:
    def __init__(self, user_service: Optional[UserService] = None):
        """
        Initialize the tool.

        Args:
            user_service: UserService instance for database operations
        """
        self.user_service = user_service

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for OpenAI API.

        Returns:
            Dict containing tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": "extract_and_save_user_name",
                "description": (
                    "Extrae el nombre del usuario de la conversación y lo guarda en la base de datos. "
                    "Si el usuario menciona o corrige su nombre, actualiza el valor correspondiente."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre completo del usuario"
                        }
                    },
                    "required": ["name"]
                }
            }
        }

    def execute(self, args: Dict[str, Any], user_id: str) -> str:
        """
        Execute the tool.

        Args:
            args: Tool arguments containing the name
            user_id: User ID to update

        Returns:
            str: Success message
        """
        try:
            name = args.get("name")
            if not name:
                return "Error: No se proporcionó un nombre válido"

            if self.user_service:
                self.user_service.update_user_name(user_id, name)
                return f"✅ Nombre '{name}' guardado correctamente."
            else:
                return "Error: UserService no disponible"

        except Exception as e:
            return f"Error al guardar el nombre: {e}"