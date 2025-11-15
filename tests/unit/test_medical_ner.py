"""
Unit tests for Medical NER
"""

import pytest
from src.entity_extraction.medical_ner import (
    MedicalNER,
    MedicalEntity,
    EntityType
)


class TestMedicalNER:
    """Test MedicalNER class"""
    
    def test_initialization(self):
        """Test NER initialization"""
        ner = MedicalNER()
        assert ner.medical_patterns is not None
        assert ner.medical_dictionary is not None
    
    def test_extract_symptoms(self):
        """Test symptom extraction"""
        ner = MedicalNER()
        text = "Patient reports fever, cough, and chest pain"
        entities = ner.extract_entities(text)
        
        symptom_entities = ner.get_entities_by_type(entities, EntityType.SYMPTOM)
        assert len(symptom_entities) > 0
        assert any("fever" in e.text.lower() for e in symptom_entities)
        assert any("cough" in e.text.lower() for e in symptom_entities)
        assert any("chest pain" in e.text.lower() for e in symptom_entities)
    
    def test_extract_diagnosis(self):
        """Test diagnosis extraction"""
        ner = MedicalNER()
        text = "Diagnosis: pneumonia and bronchitis"
        entities = ner.extract_entities(text)
        
        diagnosis_entities = ner.get_entities_by_type(entities, EntityType.DIAGNOSIS)
        assert len(diagnosis_entities) > 0
        assert any("pneumonia" in e.text.lower() for e in diagnosis_entities)
    
    def test_extract_medications(self):
        """Test medication extraction"""
        ner = MedicalNER()
        text = "Prescribed aspirin and ibuprofen"
        entities = ner.extract_entities(text)
        
        medication_entities = ner.get_entities_by_type(entities, EntityType.MEDICATION)
        assert len(medication_entities) > 0
        assert any("aspirin" in e.text.lower() for e in medication_entities)
    
    def test_extract_vital_signs(self):
        """Test vital sign extraction"""
        ner = MedicalNER()
        text = "Blood pressure: 120/80, Heart rate: 72 bpm"
        entities = ner.extract_entities(text)
        
        vital_entities = ner.get_entities_by_type(entities, EntityType.VITAL_SIGN)
        assert len(vital_entities) > 0
        assert any("blood pressure" in e.text.lower() for e in vital_entities)
        assert any("heart rate" in e.text.lower() for e in vital_entities)
    
    def test_summarize_entities(self):
        """Test entity summarization"""
        ner = MedicalNER()
        text = "Patient has fever and cough. Diagnosis: pneumonia. Prescribed aspirin."
        entities = ner.extract_entities(text)
        
        summary = ner.summarize_entities(entities)
        assert summary["total_entities"] > 0
        assert "by_type" in summary
        assert "entities" in summary

