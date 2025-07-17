from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from db.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Validate DATABASE_URL before creating engine
if not Config.DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

# Create engine with optimized settings
engine = create_engine(
    Config.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("SQLAlchemy engine and session factory initialized successfully")
