"""
Adaptive Learning Memory Module

This module implements adaptive learning capabilities for the clinical memory system:
- Automatic case addition to Qdrant
- Pattern learning and evolution
- Periodic reindexing for performance optimization
"""

from .case_ingestion import CaseIngestionOrchestrator
from .pattern_analyzer import PatternAnalyzer
from .reindexing_service import ReindexingService

__all__ = [
    "CaseIngestionOrchestrator",
    "PatternAnalyzer",
    "ReindexingService",
]

