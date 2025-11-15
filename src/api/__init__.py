"""
API Module for HygiaAI

Provides FastAPI endpoints for:
- Transcription
- Entity extraction
- Case retrieval
- RAG-based insights
- Visualization data
- EHR integration
"""

from .visualization_api import router as visualization_router
from .ehr_api import router as ehr_router
from .compliance_api import router as compliance_router

__all__ = [
    "visualization_router",
    "ehr_router",
    "compliance_router",
]

