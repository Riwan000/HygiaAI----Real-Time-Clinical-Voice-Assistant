"""
Unit tests for Medical Terminology Validator
"""

import pytest
from src.entity_extraction.medical_terminology import (
    MedicalTerminologyValidator,
    TerminologyCorrection
)


class TestMedicalTerminologyValidator:
    """Test MedicalTerminologyValidator class"""
    
    def test_initialization(self):
        """Test validator initialization"""
        validator = MedicalTerminologyValidator()
        assert validator.medical_abbreviations is not None
        assert validator.medical_corrections is not None
        assert validator.common_variations is not None
    
    def test_validate_term(self):
        """Test term validation"""
        validator = MedicalTerminologyValidator()
        
        # Valid term
        is_valid, corrected = validator.validate_term("fever")
        assert is_valid is True
        
        # Abbreviation
        is_valid, corrected = validator.validate_term("bp")
        assert is_valid is True
        assert corrected == "blood pressure"
        
        # Invalid term
        is_valid, corrected = validator.validate_term("xyzabc")
        assert is_valid is False
    
    def test_correct_text(self):
        """Test text correction"""
        validator = MedicalTerminologyValidator()
        text = "Patient has bp of 120/80 and hr of 72 bpm"
        
        corrected_text, corrections = validator.correct_text(text)
        
        assert "blood pressure" in corrected_text.lower()
        assert "heart rate" in corrected_text.lower()
        assert len(corrections) > 0
    
    def test_get_terminology_summary(self):
        """Test terminology summary"""
        validator = MedicalTerminologyValidator()
        text = "Patient has fever, cough, and bp of 120/80"
        
        summary = validator.get_terminology_summary(text)
        
        assert summary["total_words"] > 0
        assert "medical_terms" in summary
        assert "abbreviations" in summary
        assert "medical_term_ratio" in summary

