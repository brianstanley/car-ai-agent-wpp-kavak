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
        filename: Optional[str] = None,
        page_numbers: Optional[List[int]] = None,
        title: Optional[str] = None
    ) -> bool:
        """Create a new kavak_info record with automatic embedding generation using raw SQL."""
        session = self.get_session()
        try:
            # Generate embedding
            embedding = self.get_embedding(text)
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            # Insert using raw SQL like the existing scripts
            query = sql_text("""
                INSERT INTO kavak_info (
                    text, filename, page_numbers, title, embedding
                ) VALUES (
                    :text, :filename, :page_numbers, :title, :embedding
                )
            """)
            
            session.execute(query, {
                'text': text,
                'filename': filename,
                'page_numbers': page_numbers,
                'title': title,
                'embedding': embedding_str
            })
            
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
        """Search for similar kavak_info records using vector similarity."""
        session = self.get_session()
        try:
            query_embedding = self.get_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Use cosine similarity to find similar embeddings
            result = session.execute(
                sql_text("""
                    SELECT id, text, filename, page_numbers, title, 
                           1 - (embedding <=> :embedding) as similarity
                    FROM kavak_info 
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> :embedding
                    LIMIT :limit
                """),
                {'embedding': embedding_str, 'limit': limit}
            )
            
            # Convert results to KavakInfoDB objects
            similar_records = []
            for row in result:
                kavak_info = KavakInfoDB(
                    id=row.id,
                    text=row.text,
                    filename=row.filename,
                    page_numbers=row.page_numbers,
                    title=row.title
                )
                similar_records.append(kavak_info)
            
            return similar_records
        finally:
            session.close() 