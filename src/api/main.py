"""
FastAPI Main Application

Main entry point for the HygiaAI API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
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

# Import lifespan context manager
from contextlib import asynccontextmanager

_routers_loaded = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load routers after app startup to avoid blocking health checks"""
    global _routers_loaded
    
    # App startup - log that the app is ready for healthchecks
    logger.info("=" * 50)
    logger.info("HygiaAI API Server Starting...")
    logger.info("Health endpoint available at /health")
    logger.info("=" * 50)
    
    # App startup - load routers in background
    logger.info("Starting application...")
    
    def load_routers():
        """Load routers synchronously (can take time)"""
        global _routers_loaded
        try:
            routers_loaded = []
            
            try:
                from .visualization_api import router as visualization_router
                app.include_router(visualization_router)
                routers_loaded.append('visualization')
            except Exception as e:
                logger.warning(f"Failed to import visualization_router: {e}")
            
            try:
                from .ehr_api import router as ehr_router
                app.include_router(ehr_router)
                routers_loaded.append('ehr')
            except Exception as e:
                logger.warning(f"Failed to import ehr_router: {e}")
            
            try:
                from .compliance_api import router as compliance_router
                app.include_router(compliance_router)
                routers_loaded.append('compliance')
            except Exception as e:
                logger.warning(f"Failed to import compliance_router: {e}")
            
            try:
                from .clinical_memory_api import router as clinical_memory_router
                app.include_router(clinical_memory_router)
                routers_loaded.append('clinical_memory')
            except Exception as e:
                logger.warning(f"Failed to import clinical_memory_router: {e}")
            
            try:
                from .federated_api import router as federated_router
                app.include_router(federated_router)
                routers_loaded.append('federated')
            except Exception as e:
                logger.warning(f"Failed to import federated_router: {e}")
            
            try:
                from .transcription_ws_api import router as transcription_ws_router
                app.include_router(transcription_ws_router)
                routers_loaded.append('transcription')
            except Exception as e:
                logger.warning(f"Failed to import transcription_ws_router: {e}")
            
            _routers_loaded = True
            logger.info(f"Routers loaded successfully: {', '.join(routers_loaded)}")
        except Exception as e:
            logger.error(f"Error loading routers: {e}", exc_info=True)
            # Continue anyway - health check should still work
    
    # Load routers in background thread to avoid blocking startup
    import threading
    router_thread = threading.Thread(target=load_routers, daemon=True)
    router_thread.start()
    
    yield  # App is running
    
    # App shutdown
    logger.info("Shutting down application...")
    
    # Register frontend catch-all route AFTER all routers are loaded
    # This ensures API routes take precedence
    if _frontend_available:
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve frontend for all non-API routes (SPA routing)"""
            # Don't serve frontend for API routes or docs (shouldn't reach here, but safety check)
            if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Not found"}
                )
            
            # Serve index.html for SPA routing
            index_file = frontend_dist / "index.html"
            if index_file.exists():
                from fastapi.responses import FileResponse
                return FileResponse(str(index_file))
            
            return JSONResponse(
                status_code=404,
                content={"detail": "Frontend not found"}
            )

# Create FastAPI app with lifespan - routers will load AFTER startup
# This ensures the health endpoint is available immediately
app = FastAPI(
    title="HygiaAI Clinical Voice Assistant API",
    description="Real-time clinical voice assistant with transcription, entity extraction, RAG-based insights, and visualization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Define health endpoint IMMEDIATELY - before any router imports
# This ensures Railway can verify health even if routers fail to load
# Railway healthchecks come from healthcheck.railway.app hostname
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway deployment
    
    This endpoint must respond quickly without dependencies on external services.
    Railway uses this to verify the deployment is healthy.
    Returns HTTP 200 status code explicitly for Railway healthchecks.
    """
    # Simple response for Railway healthcheck - must be fast!
    return {"status": "ok"}

# Check if frontend is available
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
_frontend_available = frontend_dist.exists()

if _frontend_available:
    # Mount static files (CSS, JS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    logger.info(f"Frontend static files mounted from: {frontend_dist}")
else:
    logger.info("Frontend not found - serving API only")

@app.get("/")
async def root():
    """Root endpoint"""
    if _frontend_available:
        # Serve frontend index.html
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            from fastapi.responses import FileResponse
            return FileResponse(str(index_file))
    
    # Fallback: API info if frontend not available
    return {
        "message": "HygiaAI Clinical Voice Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "frontend": "available" if _frontend_available else "not included"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

