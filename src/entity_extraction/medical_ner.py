"""
Medical Named Entity Recognition (NER) Module

Extracts medical entities from transcripts including:
- Symptoms
- Diagnoses
- Medications
- Vital signs
- Medical procedures
- Body parts/anatomy
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of medical entities"""
    SYMPTOM = "symptom"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    VITAL_SIGN = "vital_sign"
    PROCEDURE = "procedure"
    BODY_PART = "body_part"
    CONDITION = "condition"
    DISEASE = "disease"
    LAB_TEST = "lab_test"
    UNKNOWN = "unknown"


@dataclass
class MedicalEntity:
    """Represents a detected medical entity"""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    normalized_form: Optional[str] = None
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "text": self.text,
            "entity_type": self.entity_type.value,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "normalized_form": self.normalized_form,
            "context": self.context,
        }


class MedicalNER:
    """
    Medical Named Entity Recognition system
    
    Extracts medical entities from clinical text using:
    - Pattern matching for common medical terms
    - Medical terminology dictionaries
    - Rule-based extraction
    - (Future: ML-based NER models like BioBERT)
    """
    
    def __init__(self):
        """Initialize Medical NER system"""
        self.medical_patterns = self._build_medical_patterns()
        self.medical_dictionary = self._build_medical_dictionary()
        logger.info("Medical NER system initialized")
    
    def _build_medical_patterns(self) -> Dict[EntityType, List[re.Pattern]]:
        """Build regex patterns for medical entity detection"""
        patterns = {
            EntityType.SYMPTOM: [
                re.compile(r'\b(fever|cough|pain|headache|nausea|vomiting|dizziness|fatigue|shortness of breath|chest pain|abdominal pain)\b', re.IGNORECASE),
                re.compile(r'\b(symptom|symptoms|complains? of|reports?)\s+([a-z\s]+)', re.IGNORECASE),
            ],
            EntityType.DIAGNOSIS: [
                re.compile(r'\b(diagnosis|diagnosed with|diagnosed as|diagnosis of)\s+([a-z\s]+)', re.IGNORECASE),
                re.compile(r'\b(pneumonia|diabetes|hypertension|asthma|bronchitis|infection|disease)\b', re.IGNORECASE),
            ],
            EntityType.MEDICATION: [
                re.compile(r'\b(prescribed|prescription|medication|medicine|drug|taking|on)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
                re.compile(r'\b(aspirin|ibuprofen|paracetamol|antibiotic|antihistamine|steroid)\b', re.IGNORECASE),
            ],
            EntityType.VITAL_SIGN: [
                re.compile(r'\b(blood pressure|bp|heart rate|hr|pulse|temperature|temp|respiratory rate|rr|oxygen saturation|spo2)\s*:?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
                re.compile(r'\b(\d+)\s*(bpm|beats per minute|degrees?|°[CF]|mmhg|mmHg)\b', re.IGNORECASE),
            ],
            EntityType.PROCEDURE: [
                re.compile(r'\b(surgery|operation|procedure|test|exam|examination|scan|x-ray|mri|ct scan|ultrasound)\b', re.IGNORECASE),
            ],
            EntityType.BODY_PART: [
                re.compile(r'\b(chest|abdomen|head|neck|arm|leg|back|shoulder|knee|elbow|wrist|ankle|heart|lung|liver|kidney|stomach)\b', re.IGNORECASE),
            ],
            EntityType.CONDITION: [
                re.compile(r'\b(acute|chronic|severe|mild|moderate|stable|unstable|improving|worsening)\b', re.IGNORECASE),
            ],
            EntityType.LAB_TEST: [
                re.compile(r'\b(blood test|lab test|test results?|cbc|complete blood count|glucose|cholesterol|creatinine)\b', re.IGNORECASE),
            ],
        }
        return patterns
    
    def _build_medical_dictionary(self) -> Dict[EntityType, List[str]]:
        """Build medical terminology dictionary"""
        return {
            EntityType.SYMPTOM: [
                "fever", "cough", "pain", "headache", "nausea", "vomiting",
                "dizziness", "fatigue", "shortness of breath", "chest pain",
                "abdominal pain", "back pain", "joint pain", "muscle pain",
                "sore throat", "runny nose", "congestion", "wheezing",
                "rash", "itching", "swelling", "bleeding", "diarrhea",
                "constipation", "loss of appetite", "weight loss", "weight gain"
            ],
            EntityType.DIAGNOSIS: [
                "pneumonia", "bronchitis", "asthma", "copd", "diabetes",
                "hypertension", "infection", "bacterial infection",
                "viral infection", "flu", "influenza", "common cold",
                "sinusitis", "pharyngitis", "tonsillitis", "gastritis",
                "ulcer", "arthritis", "osteoporosis", "anemia"
            ],
            EntityType.MEDICATION: [
                "aspirin", "ibuprofen", "paracetamol", "acetaminophen",
                "antibiotic", "penicillin", "amoxicillin", "antihistamine",
                "steroid", "prednisone", "insulin", "metformin",
                "antacid", "painkiller", "analgesic", "antipyretic"
            ],
            EntityType.VITAL_SIGN: [
                "blood pressure", "heart rate", "pulse", "temperature",
                "respiratory rate", "oxygen saturation", "spo2", "bp",
                "hr", "rr", "temp"
            ],
            EntityType.PROCEDURE: [
                "surgery", "operation", "biopsy", "endoscopy", "colonoscopy",
                "x-ray", "mri", "ct scan", "ultrasound", "ekg", "ecg",
                "blood test", "urine test", "stool test"
            ],
            EntityType.BODY_PART: [
                "chest", "abdomen", "head", "neck", "arm", "leg", "back",
                "shoulder", "knee", "elbow", "wrist", "ankle", "foot",
                "hand", "heart", "lung", "liver", "kidney", "stomach",
                "intestine", "brain", "spine", "bone", "muscle", "joint"
            ],
        }
    
    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from text
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of MedicalEntity objects
        """
        entities = []
        text_lower = text.lower()
        
        # Extract using patterns
        for entity_type, patterns in self.medical_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    entity_text = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Check if entity already found (avoid duplicates)
                    if not any(
                        e.start_pos == start_pos and e.end_pos == end_pos
                        for e in entities
                    ):
                        entity = MedicalEntity(
                            text=entity_text,
                            entity_type=entity_type,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            confidence=0.8,  # Pattern-based confidence
                            normalized_form=self._normalize_entity(entity_text, entity_type),
                            context=self._extract_context(text, start_pos, end_pos)
                        )
                        entities.append(entity)
        
        # Extract using dictionary lookup
        for entity_type, terms in self.medical_dictionary.items():
            for term in terms:
                # Find all occurrences of the term
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                matches = pattern.finditer(text)
                for match in matches:
                    entity_text = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Check if entity already found
                    if not any(
                        e.start_pos == start_pos and e.end_pos == end_pos
                        for e in entities
                    ):
                        entity = MedicalEntity(
                            text=entity_text,
                            entity_type=entity_type,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            confidence=0.9,  # Dictionary-based confidence
                            normalized_form=self._normalize_entity(entity_text, entity_type),
                            context=self._extract_context(text, start_pos, end_pos)
                        )
                        entities.append(entity)
        
        # Sort by position
        entities.sort(key=lambda e: e.start_pos)
        
        # Remove overlapping entities (prefer longer, higher confidence entities)
        entities = self._deduplicate_entities(entities)
        
        logger.debug(f"Extracted {len(entities)} medical entities from text")
        return entities
    
    def _deduplicate_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """
        Remove overlapping entities, keeping the best ones
        
        Args:
            entities: List of entities (should be sorted by position)
            
        Returns:
            Deduplicated list of entities
        """
        if not entities:
            return entities
        
        deduplicated = []
        
        for entity in entities:
            # Check if this entity overlaps with any already added entity
            overlaps = False
            for existing in deduplicated:
                # Check for overlap
                if not (entity.end_pos <= existing.start_pos or entity.start_pos >= existing.end_pos):
                    # There's overlap - keep the better one
                    # Prefer: longer entity, higher confidence, dictionary-based over pattern-based
                    entity_score = (
                        len(entity.text),  # Length
                        entity.confidence,  # Confidence
                        1 if entity.confidence >= 0.9 else 0  # Dictionary vs pattern
                    )
                    existing_score = (
                        len(existing.text),
                        existing.confidence,
                        1 if existing.confidence >= 0.9 else 0
                    )
                    
                    if entity_score > existing_score:
                        # Replace existing with this entity
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(entity)
        
        # Sort again by position
        deduplicated.sort(key=lambda e: e.start_pos)
        
        return deduplicated
    
    def _normalize_entity(self, text: str, entity_type: EntityType) -> str:
        """
        Normalize entity text to standard form
        
        Args:
            text: Entity text
            entity_type: Type of entity
            
        Returns:
            Normalized entity text
        """
        # Basic normalization
        normalized = text.lower().strip()
        
        # Entity-specific normalization
        if entity_type == EntityType.VITAL_SIGN:
            # Normalize vital sign abbreviations
            normalized = normalized.replace("bp", "blood pressure")
            normalized = normalized.replace("hr", "heart rate")
            normalized = normalized.replace("rr", "respiratory rate")
            normalized = normalized.replace("spo2", "oxygen saturation")
            normalized = normalized.replace("temp", "temperature")
        
        return normalized
    
    def _extract_context(self, text: str, start_pos: int, end_pos: int, context_window: int = 50) -> str:
        """
        Extract context around entity
        
        Args:
            text: Full text
            start_pos: Start position of entity
            end_pos: End position of entity
            context_window: Number of characters before/after to include
            
        Returns:
            Context string
        """
        context_start = max(0, start_pos - context_window)
        context_end = min(len(text), end_pos + context_window)
        return text[context_start:context_end]
    
    def get_entities_by_type(self, entities: List[MedicalEntity], entity_type: EntityType) -> List[MedicalEntity]:
        """
        Filter entities by type
        
        Args:
            entities: List of entities
            entity_type: Type to filter by
            
        Returns:
            Filtered list of entities
        """
        return [e for e in entities if e.entity_type == entity_type]
    
    def summarize_entities(self, entities: List[MedicalEntity]) -> Dict[str, Any]:
        """
        Summarize extracted entities
        
        Args:
            entities: List of entities
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_entities": len(entities),
            "by_type": {},
            "entities": [e.to_dict() for e in entities]
        }
        
        # Count by type
        for entity_type in EntityType:
            type_entities = [e for e in entities if e.entity_type == entity_type]
            count = len(type_entities)
            if count > 0:
                summary["by_type"][entity_type.value] = count
        
        return summary

