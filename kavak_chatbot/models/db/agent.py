from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from db.session import Base

class AgentDB(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instruction = Column(String, nullable=False)
    application_mode = Column(String, default="assistant")
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=True)
    tools = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.utcnow)

    # Relationship
    persona = relationship("PersonaDB", back_populates="agents")