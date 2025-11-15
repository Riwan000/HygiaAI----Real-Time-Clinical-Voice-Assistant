"""
Transcript Processing Module

Handles post-processing of transcripts including:
- Medical terminology validation
- Medical entity extraction (NER)
- Spell-checking for medical terms
- Speaker identification
- Timestamp management
- Storage preparation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..entity_extraction import (
    MedicalNER,
    MedicalTerminologyValidator,
    MedicalSpellChecker,
    MedicalEntity,
    EntityType,
    EntityEvaluator,
    EvaluationMetrics
)

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """
    Processes and validates transcription results
    """
    
    def __init__(self, enable_validation: bool = True):
        """
        Initialize transcript processor
        
        Args:
            enable_validation: Whether to enable entity extraction validation
        """
        self.medical_ner = MedicalNER()
        self.terminology_validator = MedicalTerminologyValidator()
        self.spell_checker = MedicalSpellChecker()
        self.medical_terms_cache = set()  # Cache for medical terminology validation
        self.enable_validation = enable_validation
        self.evaluator = EntityEvaluator() if enable_validation else None
    
    def process_transcript(
        self,
        transcript_data: Dict[str, Any],
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a single transcript result
        
        Args:
            transcript_data: Raw transcript data from Deepgram
            session_metadata: Optional session metadata (patient_id, doctor_id, etc.)
            
        Returns:
            Processed transcript with metadata
        """
        transcript_text = transcript_data.get("transcript", "")
        
        # Process transcript with medical terminology validation
        corrected_text = transcript_text
        corrections = []
        entities = []
        
        if transcript_text:
            # Step 1: Spell-check medical terms
            corrected_text, spell_corrections = self.spell_checker.correct_text(transcript_text)
            corrections.extend(spell_corrections)
            
            # Step 2: Validate and correct medical terminology
            validated_text, term_corrections = self.terminology_validator.correct_text(corrected_text)
            corrected_text = validated_text
            corrections.extend(term_corrections)
            
            # Step 3: Extract medical entities using NER
            entities = self.medical_ner.extract_entities(corrected_text)
            
            # Step 4: Get medical terms summary
            terminology_summary = self.terminology_validator.get_terminology_summary(corrected_text)
        
        processed = {
            "transcript": corrected_text,  # Use corrected text
            "original_transcript": transcript_text,  # Keep original for reference
            "is_final": transcript_data.get("is_final", False),
            "confidence": transcript_data.get("confidence"),
            "speaker": transcript_data.get("speaker"),
            "timestamp": transcript_data.get("timestamp"),
            "session_id": transcript_data.get("session_id"),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": session_metadata or {},
            "medical_entities": [e.to_dict() for e in entities],
            "medical_terms_detected": [e.text for e in entities],
            "corrections": [
                {
                    "original": c.original,
                    "corrected": c.corrected,
                    "confidence": c.confidence,
                    "type": getattr(c, 'correction_type', 'spelling')
                }
                for c in corrections
            ],
            "terminology_summary": terminology_summary if transcript_text else {},
        }
        
        return processed
    
    def extract_medical_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from text using NER
        
        Args:
            text: Transcript text
            
        Returns:
            List of MedicalEntity objects
        """
        return self.medical_ner.extract_entities(text)
    
    def get_entities_by_type(self, entities: List[MedicalEntity], entity_type: EntityType) -> List[MedicalEntity]:
        """
        Filter entities by type
        
        Args:
            entities: List of entities
            entity_type: Type to filter by
            
        Returns:
            Filtered list of entities
        """
        return self.medical_ner.get_entities_by_type(entities, entity_type)
    
    def merge_interim_results(
        self,
        interim_results: List[Dict[str, Any]]
    ) -> str:
        """
        Merge multiple interim transcription results into final transcript
        
        Args:
            interim_results: List of interim transcript results
            
        Returns:
            Merged transcript text
        """
        if not interim_results:
            return ""
        
        # Sort by timestamp if available
        sorted_results = sorted(
            interim_results,
            key=lambda x: x.get("timestamp", 0)
        )
        
        # Merge transcripts
        merged = " ".join(
            result.get("transcript", "")
            for result in sorted_results
        )
        
        return merged.strip()
    
    def validate_entities(
        self,
        predicted_entities: List[MedicalEntity],
        ground_truth_entities: Optional[List[MedicalEntity]] = None
    ) -> Optional[EvaluationMetrics]:
        """
        Validate extracted entities against ground truth
        
        Args:
            predicted_entities: List of predicted entities
            ground_truth_entities: Optional list of ground truth entities for validation
            
        Returns:
            EvaluationMetrics if ground truth provided, None otherwise
        """
        if not self.enable_validation or not self.evaluator:
            return None
        
        if ground_truth_entities is None:
            logger.debug("No ground truth entities provided for validation")
            return None
        
        metrics = self.evaluator.evaluate(predicted_entities, ground_truth_entities)
        logger.info(
            f"Entity validation: Precision={metrics.precision:.4f}, "
            f"Recall={metrics.recall:.4f}, F1={metrics.f1_score:.4f}"
        )
        return metrics
    
    def generate_validation_report(
        self,
        metrics: EvaluationMetrics,
        detailed: bool = True
    ) -> str:
        """
        Generate validation report from evaluation metrics
        
        Args:
            metrics: EvaluationMetrics object
            detailed: Whether to include detailed per-type metrics
            
        Returns:
            Formatted report string
        """
        if not self.enable_validation or not self.evaluator:
            return "Validation is disabled"
        
        return self.evaluator.generate_report(metrics, detailed=detailed)
    
    def format_for_storage(
        self,
        processed_transcript: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format transcript for storage in Qdrant
        
        Args:
            processed_transcript: Processed transcript data
            
        Returns:
            Formatted data ready for Qdrant storage
        """
        return {
            "modality": "text",
            "transcript": processed_transcript.get("transcript"),
            "original_transcript": processed_transcript.get("original_transcript"),
            "session_id": processed_transcript.get("session_id"),
            "timestamp": processed_transcript.get("timestamp"),
            "speaker": processed_transcript.get("speaker"),
            "confidence": processed_transcript.get("confidence"),
            "medical_entities": processed_transcript.get("medical_entities", []),
            "medical_terms": processed_transcript.get("medical_terms_detected", []),
            "corrections": processed_transcript.get("corrections", []),
            "terminology_summary": processed_transcript.get("terminology_summary", {}),
            "metadata": processed_transcript.get("metadata", {}),
            "processed_at": processed_transcript.get("processed_at"),
        }

