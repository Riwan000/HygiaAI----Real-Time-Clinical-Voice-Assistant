"""
Medical Entity Extraction Module

Handles:
- Named Entity Recognition (NER) for medical entities
- Medical terminology validation
- Spell-checking for medical terms
- Entity extraction and classification
- Evaluation metrics for entity extraction
"""

from .medical_ner import MedicalNER, MedicalEntity, EntityType
from .medical_terminology import MedicalTerminologyValidator
from .spell_checker import MedicalSpellChecker
from .evaluation import EntityEvaluator, EvaluationMetrics, EntityMatch
from .soap_generator import SOAPGenerator, SOAPNote

__all__ = [
    "MedicalNER",
    "MedicalEntity",
    "EntityType",
    "MedicalTerminologyValidator",
    "MedicalSpellChecker",
    "EntityEvaluator",
    "EvaluationMetrics",
    "EntityMatch",
    "SOAPGenerator",
    "SOAPNote",
]

