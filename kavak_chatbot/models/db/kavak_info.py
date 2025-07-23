from sqlalchemy import Column, String, DateTime, Text, ARRAY, Integer
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime, UTC
from db.session import Base

class KavakInfoDB(Base):
    __tablename__ = "kavak_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    title = Column(String, nullable=True)
    meta = Column(ARRAY(String), nullable=True)  # Store metadata as an array of strings
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small has 1536 dimensions
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime,  default=datetime.now(UTC), onupdate=datetime.now(UTC))