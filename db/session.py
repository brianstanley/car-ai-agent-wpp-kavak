from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
from db.config import Config

logger = logging.getLogger(__name__)

if not Config.DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

# Create engine with optimized settings
engine = create_engine(
    Config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("SQLAlchemy engine and session factory initialized successfully")

# Global Base for all models
Base = declarative_base()
