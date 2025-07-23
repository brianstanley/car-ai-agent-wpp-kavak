from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from db.session import engine, SessionLocal


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for PostgreSQL with pgvector support using SQLAlchemy."""

    def __init__(self):
        # Use the centralized engine and session factory from session.py
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """Test database connection."""
        if not self.engine:
            logger.error("Engine not initialized")
            return False

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        if not self.engine:
            logger.error("Engine not initialized")
            return []

        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"Found {len(tables)} tables: {tables}")
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        if not self.engine:
            logger.error("Engine not initialized")
            return {}

        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)

            column_info = []
            for col in columns:
                column_info.append({
                    "column_name": col["name"],
                    "data_type": str(col["type"]),
                    "is_nullable": "YES" if col.get("nullable", True) else "NO",
                    "column_default": str(col.get("default", "")) if col.get("default") else None
                })

            return {
                "table_name": table_name,
                "columns": column_info
            }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {}

    def check_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed."""
        if not self.engine:
            logger.error("Engine not initialized")
            return False

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking pgvector extension: {e}")
            return False

    def close(self):
        logger.info("DatabaseManager instance closed")