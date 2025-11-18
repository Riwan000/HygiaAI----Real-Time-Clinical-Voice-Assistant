"""
FastAPI Main Application

Main entry point for the HygiaAI API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from pathlib import Path

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
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway deployment
    
    This endpoint must respond quickly without dependencies on external services.
    Railway uses this to verify the deployment is healthy.
    """
    return {
        "status": "healthy",
        "service": "HygiaAI API",
        "version": "1.0.0"
    }

# Serve static files (frontend) if they exist
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_path / "assets")), name="assets")
    
    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """
        Serve frontend files. If path doesn't exist, serve index.html for SPA routing.
        API routes are handled by routers, so they won't reach here.
        """
        # Don't serve frontend for API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return {"error": "Not found"}
        
        # Check if it's a file in dist
        file_path = frontend_dist_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # For SPA routing, serve index.html
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        
        return {"error": "Not found"}
else:
    # If frontend not built, just return API info
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "HygiaAI Clinical Voice Assistant API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "note": "Frontend not built. Build frontend and place dist/ in frontend/dist/"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

