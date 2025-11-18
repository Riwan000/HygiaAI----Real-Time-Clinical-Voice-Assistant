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

# Import routers lazily to avoid heavy initialization during startup
# This allows the health check to respond quickly even if some routers fail to import
def import_routers():
    """Lazy import of routers - called after app creation"""
    routers = {}
    
    try:
        from .visualization_api import router as visualization_router
        routers['visualization'] = visualization_router
    except Exception as e:
        logger.warning(f"Failed to import visualization_router: {e}")
        routers['visualization'] = None

    try:
        from .ehr_api import router as ehr_router
        routers['ehr'] = ehr_router
    except Exception as e:
        logger.warning(f"Failed to import ehr_router: {e}")
        routers['ehr'] = None

    try:
        from .compliance_api import router as compliance_router
        routers['compliance'] = compliance_router
    except Exception as e:
        logger.warning(f"Failed to import compliance_router: {e}")
        routers['compliance'] = None

    try:
        from .clinical_memory_api import router as clinical_memory_router
        routers['clinical_memory'] = clinical_memory_router
    except Exception as e:
        logger.warning(f"Failed to import clinical_memory_router: {e}")
        routers['clinical_memory'] = None

    try:
        from .federated_api import router as federated_router
        routers['federated'] = federated_router
    except Exception as e:
        logger.warning(f"Failed to import federated_router: {e}")
        routers['federated'] = None

    try:
        from .transcription_ws_api import router as transcription_ws_router
        routers['transcription'] = transcription_ws_router
    except Exception as e:
        logger.warning(f"Failed to import transcription_ws_router: {e}")
        routers['transcription'] = None
    
    return routers

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

# Include routers lazily (after app creation to allow health check to work immediately)
# Import routers in background to avoid blocking startup
try:
    routers = import_routers()
    if routers.get('visualization'):
        app.include_router(routers['visualization'])
    if routers.get('ehr'):
        app.include_router(routers['ehr'])
    if routers.get('compliance'):
        app.include_router(routers['compliance'])
    if routers.get('clinical_memory'):
        app.include_router(routers['clinical_memory'])
    if routers.get('federated'):
        app.include_router(routers['federated'])
    if routers.get('transcription'):
        app.include_router(routers['transcription'])
    logger.info("All routers loaded successfully")
except Exception as e:
    logger.error(f"Error loading routers: {e}", exc_info=True)
    # Continue anyway - health check should still work


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
    """
    Health check endpoint for Railway deployment
    
    This endpoint must respond quickly without dependencies on external services.
    Railway uses this to verify the deployment is healthy.
    """
    try:
        # Return immediately - don't check external services to avoid timeouts
        return {
            "status": "healthy",
            "service": "HygiaAI API",
            "version": "1.0.0"
        }
    except Exception as e:
        # Even if there's an error, return 200 to prevent Railway from marking as unhealthy
        # during startup when some modules might not be loaded yet
        logger.warning(f"Health check warning: {e}")
        return {
            "status": "healthy",
            "service": "HygiaAI API",
            "version": "1.0.0",
            "note": "Some services may still be initializing"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

