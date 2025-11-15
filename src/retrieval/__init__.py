"""
Contextual Retrieval Module

Handles:
- Semantic search for clinical cases
- Keyword-based search with filters
- Hybrid search (semantic + keyword)
- Case ranking and filtering
- Clinical case retrieval
"""

from .case_retrieval import CaseRetriever, RetrievalResult, RetrievalOptions, RetrievalMode

__all__ = [
    "CaseRetriever",
    "RetrievalResult",
    "RetrievalOptions",
    "RetrievalMode",
]

