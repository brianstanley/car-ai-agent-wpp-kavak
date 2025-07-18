from sqlalchemy import Column, String, DateTime, Text, ARRAY, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from db.session import Base

class KavakInfoDB(Base):
    __tablename__ = "kavak_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    filename = Column(String, nullable=True)
    page_numbers = Column(ARRAY(Integer), nullable=True)
    title = Column(String, nullable=True)
    # Note: embedding column is handled via raw SQL in the service
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 