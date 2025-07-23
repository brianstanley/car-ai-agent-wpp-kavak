import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the chatbot memory system."""

    DATABASE_URL = os.getenv("DATABASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TOKEN_THRESHOLD = int(os.getenv("TOKEN_THRESHOLD", "4000"))

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in environment variables")

        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required in environment variables")