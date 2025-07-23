from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class Persona(BaseModel):
    """Model for chatbot personas."""
    id: Optional[UUID] = None
    name: str
    role: str
    goals: Optional[str] = None
    background: Optional[str] = None
    def generate_system_prompt_input(self) -> str:
        prompt_parts = []
        if self.name:
            prompt_parts.append(f"Tu eres {self.name}.")
        if self.role:
            prompt_parts.append(f"Tu rol es: {self.role}.")
        if self.goals:
            prompt_parts.append(f"Tus objetivos son: {self.goals}.")
        if self.background:
            prompt_parts.append(f"Tu experiencia es: {self.background}.")
        return " ".join(prompt_parts)