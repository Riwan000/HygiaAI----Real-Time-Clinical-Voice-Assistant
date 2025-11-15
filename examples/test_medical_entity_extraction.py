"""
Example: Testing Medical Entity Extraction

Demonstrates:
- Medical NER (Named Entity Recognition)
- Medical terminology validation
- Spell-checking for medical terms
- Entity extraction and classification
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.entity_extraction import (
    MedicalNER,
    MedicalTerminologyValidator,
    MedicalSpellChecker,
    EntityType
)
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


def test_medical_ner():
    """Test medical NER extraction"""
    print("=" * 60)
    print("Test 1: Medical Named Entity Recognition (NER)")
    print("=" * 60)
    print()
    
    ner = MedicalNER()
    
    # Sample clinical transcript
    transcript = """
    Patient reports fever, cough, and chest pain for the past 3 days.
    Blood pressure: 140/90 mmHg, Heart rate: 88 bpm, Temperature: 38.5°C.
    Diagnosis: pneumonia and bronchitis.
    Prescribed aspirin 100mg and ibuprofen 200mg.
    Recommended chest X-ray and blood test.
    """
    
    print("Sample Transcript:")
    print(transcript)
    print()
    
    # Extract entities
    entities = ner.extract_entities(transcript)
    
    print(f"✓ Extracted {len(entities)} medical entities")
    print()
    
    # Group by type
    print("Entities by Type:")
    for entity_type in EntityType:
        type_entities = ner.get_entities_by_type(entities, entity_type)
        if type_entities:
            print(f"  {entity_type.value}: {len(type_entities)}")
            for entity in type_entities[:3]:  # Show first 3
                print(f"    - {entity.text} (confidence: {entity.confidence:.2f})")
    print()
    
    # Summary
    summary = ner.summarize_entities(entities)
    print("Entity Summary:")
    print(f"  Total Entities: {summary['total_entities']}")
    print(f"  By Type: {summary['by_type']}")
    print()


def test_terminology_validation():
    """Test medical terminology validation"""
    print("=" * 60)
    print("Test 2: Medical Terminology Validation")
    print("=" * 60)
    print()
    
    validator = MedicalTerminologyValidator()
    
    # Sample text with abbreviations and misspellings
    text = "Patient has bp of 120/80, hr of 72 bpm, and temp of 37.5°C. Diagnosed with diabetis."
    
    print("Original Text:")
    print(f"  {text}")
    print()
    
    # Correct terminology
    corrected_text, corrections = validator.correct_text(text)
    
    print("Corrected Text:")
    print(f"  {corrected_text}")
    print()
    
    print("Corrections Applied:")
    for correction in corrections:
        print(f"  - {correction.original} → {correction.corrected} ({correction.correction_type}, confidence: {correction.confidence:.2f})")
    print()
    
    # Terminology summary
    summary = validator.get_terminology_summary(corrected_text)
    print("Terminology Summary:")
    print(f"  Total Words: {summary['total_words']}")
    print(f"  Medical Terms: {len(summary['medical_terms'])}")
    print(f"  Abbreviations: {len(summary['abbreviations'])}")
    print(f"  Medical Term Ratio: {summary['medical_term_ratio']:.2%}")
    print()


def test_spell_checking():
    """Test medical spell checking"""
    print("=" * 60)
    print("Test 3: Medical Spell Checking")
    print("=" * 60)
    print()
    
    checker = MedicalSpellChecker()
    
    # Sample text with misspellings
    text = "Patient has diabetis, hypertention, and pneumonitis. Presciption for medcation."
    
    print("Original Text:")
    print(f"  {text}")
    print()
    
    # Correct spelling
    corrected_text, corrections = checker.correct_text(text)
    
    print("Corrected Text:")
    print(f"  {corrected_text}")
    print()
    
    print("Spell Corrections:")
    for correction in corrections:
        print(f"  - {correction.original} → {correction.corrected} (confidence: {correction.confidence:.2f})")
    print()
    
    # Get suggestions for misspelled words
    print("Spelling Suggestions:")
    misspelled_words = ["diabetis", "hypertention", "pneumonitis"]
    for word in misspelled_words:
        suggestions = checker.get_suggestions(word)
        print(f"  {word}: {suggestions}")
    print()


def test_integrated_processing():
    """Test integrated processing pipeline"""
    print("=" * 60)
    print("Test 4: Integrated Processing Pipeline")
    print("=" * 60)
    print()
    
    ner = MedicalNER()
    validator = MedicalTerminologyValidator()
    checker = MedicalSpellChecker()
    
    # Sample transcript with errors
    transcript = "Patient reports fevr and caugh. BP: 140/90, HR: 88. Diagnosed with pneumonitis. Presciption for aspirin."
    
    print("Original Transcript:")
    print(f"  {transcript}")
    print()
    
    # Step 1: Spell-check
    corrected_text, spell_corrections = checker.correct_text(transcript)
    print("After Spell-Checking:")
    print(f"  {corrected_text}")
    print(f"  Corrections: {len(spell_corrections)}")
    print()
    
    # Step 2: Terminology validation
    validated_text, term_corrections = validator.correct_text(corrected_text)
    print("After Terminology Validation:")
    print(f"  {validated_text}")
    print(f"  Corrections: {len(term_corrections)}")
    print()
    
    # Step 3: Entity extraction
    entities = ner.extract_entities(validated_text)
    print("Extracted Entities:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.entity_type.value}, confidence: {entity.confidence:.2f})")
    print()
    
    # Summary
    summary = ner.summarize_entities(entities)
    print("Final Summary:")
    print(f"  Total Corrections: {len(spell_corrections) + len(term_corrections)}")
    print(f"  Total Entities: {summary['total_entities']}")
    print(f"  Entity Types: {list(summary['by_type'].keys())}")
    print()


def main():
    """Run all medical entity extraction tests"""
    print()
    print("=" * 60)
    print("Medical Entity Extraction Test Suite")
    print("=" * 60)
    print()
    
    test_medical_ner()
    test_terminology_validation()
    test_spell_checking()
    test_integrated_processing()
    
    print("=" * 60)
    print("✅ All medical entity extraction tests completed!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()

