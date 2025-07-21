"""
    Module for database models.
"""
from models.db.chat_session import ChatSessionDB
from models.db.conversation_memory import ConversationMemoryDB
from models.db.summary import SummaryDB
from models.db.user import UserDB
from models.db.agent import AgentDB
from models.db.persona import PersonaDB
from models.db.kavak_info import KavakInfoDB
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text
from pgvector.sqlalchemy import Vector
from db.session import Base

class CarDB(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String)
    km = Column(Integer)
    price = Column(Numeric)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    version = Column(String)
    bluetooth = Column(Boolean)
    largo = Column(Numeric)
    ancho = Column(Numeric)
    altura = Column(Numeric)
    car_play = Column(Boolean)
    descripcion = Column(Text)
    embedding = Column(Vector(1536))

__all__ =  [
    "UserDB",
    "ChatSessionDB",
    "ConversationMemoryDB",
    "SummaryDB",
    "AgentDB",
    "PersonaDB",
    "KavakInfoDB"
]

