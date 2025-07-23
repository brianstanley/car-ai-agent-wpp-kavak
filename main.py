"""
FastAPI application with organized API structure and versioning.
"""

import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import api_v1_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kavak WhatsApp Bot API",
    description="API for Kavak WhatsApp Bot with organized endpoints and versioning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Kavak WhatsApp Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_v1": "/api/v1"
    }

# Health check at root level (legacy compatibility)
@app.get("/health")
async def health_check():
    """Legacy health check endpoint."""
    return {"status": "healthy", "service": "Kavak WhatsApp Bot"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)