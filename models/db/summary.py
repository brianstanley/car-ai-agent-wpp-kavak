from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from db.session import Base

class SummaryDB(Base):
    __tablename__ = "summaries_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON field for embedding data