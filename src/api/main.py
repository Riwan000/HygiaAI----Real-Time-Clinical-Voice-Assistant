"""
FastAPI Main Application

Main entry point for the HygiaAI API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Try to load environment variables from .env file (if exists)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers with error handling
visualization_router = None
ehr_router = None
compliance_router = None
clinical_memory_router = None
federated_router = None
transcription_ws_router = None

try:
    from .visualization_api import router as visualization_router
except Exception as e:
    logger.warning(f"Failed to import visualization_router: {e}")

try:
    from .ehr_api import router as ehr_router
except Exception as e:
    logger.warning(f"Failed to import ehr_router: {e}")

try:
    from .compliance_api import router as compliance_router
except Exception as e:
    logger.warning(f"Failed to import compliance_router: {e}")

try:
    from .clinical_memory_api import router as clinical_memory_router
except Exception as e:
    logger.warning(f"Failed to import clinical_memory_router: {e}")

try:
    from .federated_api import router as federated_router
except Exception as e:
    logger.warning(f"Failed to import federated_router: {e}")

try:
    from .transcription_ws_api import router as transcription_ws_router
except Exception as e:
    logger.warning(f"Failed to import transcription_ws_router: {e}")

# Create FastAPI app
app = FastAPI(
    title="HygiaAI Clinical Voice Assistant API",
    description="Real-time clinical voice assistant with transcription, entity extraction, RAG-based insights, and visualization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
# Note: Cannot use allow_origins=["*"] with allow_credentials=True
# For development, we allow all origins without credentials
# For production, specify exact origins: allow_origins=["https://yourdomain.com"]

# Get allowed origins from environment variable or default to wildcard for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if allowed_origins == ["*"]:
    allow_creds = False
else:
    allow_creds = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, set ALLOWED_ORIGINS env var
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (only if they imported successfully)
if visualization_router:
    app.include_router(visualization_router)
if ehr_router:
    app.include_router(ehr_router)
if compliance_router:
    app.include_router(compliance_router)
if clinical_memory_router:
    app.include_router(clinical_memory_router)
if federated_router:
    app.include_router(federated_router)
if transcription_ws_router:
    app.include_router(transcription_ws_router)


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

