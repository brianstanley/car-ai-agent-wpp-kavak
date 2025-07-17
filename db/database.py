import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from db.config import Config

class DatabaseManager:
    """Database manager for PostgreSQL with pgvector support."""

    def __init__(self):
        self.connection_string = Config.DATABASE_URL

    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    return tables
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    columns = cursor.fetchall()
                    return {
                        "table_name": table_name,
                        "columns": [dict(col) for col in columns]
                    }
        except Exception as e:
            print(f"Error getting table info for {table_name}: {e}")
            return {}

    def check_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                    return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking pgvector extension: {e}")
            return False