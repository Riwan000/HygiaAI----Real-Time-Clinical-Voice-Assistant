"""
FastAPI Main Application

Main entry point for the HygiaAI API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .visualization_api import router as visualization_router
from .ehr_api import router as ehr_router
from .compliance_api import router as compliance_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HygiaAI Clinical Voice Assistant API",
    description="Real-time clinical voice assistant with transcription, entity extraction, RAG-based insights, and visualization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(visualization_router)
app.include_router(ehr_router)
app.include_router(compliance_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HygiaAI Clinical Voice Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "HygiaAI API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

