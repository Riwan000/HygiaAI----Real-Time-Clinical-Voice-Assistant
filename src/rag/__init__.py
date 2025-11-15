"""
RAG-Based Clinical Insight Generation Module

Handles:
- Context retrieval and aggregation
- LLM integration for clinical reasoning
- Clinical insight generation
- Recommendation generation with citations
- Explainable recommendations
"""

from .clinical_rag import ClinicalRAG, ClinicalInsight, Recommendation, RAGOptions

__all__ = [
    "ClinicalRAG",
    "ClinicalInsight",
    "Recommendation",
    "RAGOptions",
]

