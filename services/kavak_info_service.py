from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from models.db.kavak_info import KavakInfoDB
from db.session import SessionLocal
from openai import OpenAI
import os

class KavakInfoService:
    """Service for managing Kavak information in the database."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_session(self) -> Session:
        """Get a database session."""
        return SessionLocal()

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def create_kavak_info_with_embedding(
            self,
            text: str,
            metadata: Optional[List[str]] = None,
            title: Optional[str] = None
    ) -> bool:
        """Create a new kavak_info record with automatic embedding generation using SQLAlchemy."""
        session = self.get_session()
        try:
            embedding = self.get_embedding(text)  # List[float]

            # Create new KavakInfoDB instance with embedding
            kavak_info = KavakInfoDB(
                text=text,
                title=title,
                meta=metadata,
                embedding=embedding  # pgvector will handle the conversion
            )

            session.add(kavak_info)
            session.commit()
            return True

        except Exception as e:
            print(f"❌ Error creating kavak_info record: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_all_kavak_info(self) -> List[KavakInfoDB]:
        """Get all kavak_info records."""
        session = self.get_session()
        try:
            return session.query(KavakInfoDB).all()
        finally:
            session.close()

    def search_similar(self, query: str, limit: int = 5) -> List[KavakInfoDB]:
        """Search for similar kavak_info records using vector cosine similarity with SQLAlchemy."""
        session = self.get_session()
        try:
            query_embedding = self.get_embedding(query)  # List[float]

            # Use SQLAlchemy with pgvector for vectorial search
            # Using cosine distance (<=>) and ordering by similarity
            similar_records = (
                session.query(KavakInfoDB)
                .filter(KavakInfoDB.embedding.isnot(None))
                .order_by(KavakInfoDB.embedding.cosine_distance(query_embedding))
                .limit(limit)
                .all()
            )

            return similar_records
        finally:
            session.close()
