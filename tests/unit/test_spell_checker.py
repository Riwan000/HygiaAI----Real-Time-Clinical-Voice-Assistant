"""
Unit tests for Medical Spell Checker
"""

import pytest
from src.entity_extraction.spell_checker import (
    MedicalSpellChecker,
    SpellCorrection
)


class TestMedicalSpellChecker:
    """Test MedicalSpellChecker class"""
    
    def test_initialization(self):
        """Test spell checker initialization"""
        checker = MedicalSpellChecker()
        assert checker.medical_dictionary is not None
        assert len(checker.medical_dictionary) > 0
    
    def test_check_spelling(self):
        """Test spelling check"""
        checker = MedicalSpellChecker()
        
        # Correct spelling
        is_correct, corrected, confidence = checker.check_spelling("fever")
        assert is_correct is True
        
        # Misspelling
        is_correct, corrected, confidence = checker.check_spelling("diabetis")
        assert is_correct is False
        assert corrected == "diabetes"
    
    def test_correct_text(self):
        """Test text correction"""
        checker = MedicalSpellChecker()
        text = "Patient has diabetis and hypertention"
        
        corrected_text, corrections = checker.correct_text(text)
        
        assert "diabetes" in corrected_text.lower()
        assert len(corrections) > 0
    
    def test_get_suggestions(self):
        """Test spelling suggestions"""
        checker = MedicalSpellChecker()
        
        suggestions = checker.get_suggestions("diabetis")
        assert len(suggestions) > 0
        assert "diabetes" in suggestions

