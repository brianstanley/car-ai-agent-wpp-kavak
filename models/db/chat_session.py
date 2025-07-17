from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime, UTC

Base = declarative_base()

class ChatSessionDB(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=True)
    started_at = Column(DateTime, default=datetime.now(UTC))
    ended_at = Column(DateTime, nullable=True)