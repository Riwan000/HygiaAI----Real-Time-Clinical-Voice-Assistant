"""
Quick Test Script for Storage Integration

Tests storage functionality without requiring Qdrant to be running.
Tests encryption, de-identification, and schema.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.storage import (
    EncryptionManager,
    DeIdentificationManager,
    StorageMetadata,
    ModalityType
)
from src.transcription.transcript_processor import TranscriptProcessor
from src.utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO")


def test_encryption():
    """Test encryption functionality"""
    print("=" * 60)
    print("Test 1: Encryption")
    print("=" * 60)
    
    manager = EncryptionManager()
    
    # Test encryption/decryption
    original = "Patient has fever and cough. Patient ID: P12345"
    encrypted = manager.encrypt(original)
    decrypted = manager.decrypt(encrypted)
    
    print(f"Original: {original}")
    print(f"Encrypted: {encrypted[:50]}...")
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == original, "Decryption failed!"
    print("✓ Encryption test passed!")
    print()


def test_deidentification():
    """Test de-identification functionality"""
    print("=" * 60)
    print("Test 2: De-Identification")
    print("=" * 60)
    
    manager = DeIdentificationManager()
    
    # Test de-identification
    text = "Patient email: john@example.com, phone: 555-123-4567, SSN: 123-45-6789"
    deidentified = manager.deidentify_text(text)
    
    print(f"Original: {text}")
    print(f"De-identified: {deidentified}")
    
    assert "[REDACTED]" in deidentified, "De-identification failed!"
    assert "john@example.com" not in deidentified, "Email not redacted!"
    assert "555-123-4567" not in deidentified, "Phone not redacted!"
    
    # Test patient ID hashing
    patient_id = "P12345"
    hashed = manager.hash_patient_id(patient_id)
    
    print(f"\nPatient ID Hashing:")
    print(f"  Original: {patient_id}")
    print(f"  Hashed: {hashed}")
    
    assert hashed != patient_id, "Hashing failed!"
    assert len(hashed) == 16, "Hash length incorrect!"
    
    print("✓ De-identification test passed!")
    print()


def test_storage_schema():
    """Test storage schema"""
    print("=" * 60)
    print("Test 3: Storage Schema")
    print("=" * 60)
    
    # Create metadata
    metadata = StorageMetadata(
        session_id="test-session-1",
        patient_id="P12345",
        doctor_id="D001",
        modality=ModalityType.TEXT,
        confidence=0.95,
        speaker="doctor"
    )
    
    print("Storage Metadata:")
    print(f"  Session ID: {metadata.session_id}")
    print(f"  Patient ID: {metadata.patient_id}")
    print(f"  Doctor ID: {metadata.doctor_id}")
    print(f"  Modality: {metadata.modality.value}")
    print(f"  Confidence: {metadata.confidence}")
    
    # Convert to dict
    metadata_dict = metadata.to_dict()
    
    print("\nMetadata Dictionary:")
    for key, value in metadata_dict.items():
        print(f"  {key}: {value}")
    
    assert metadata_dict["session_id"] == "test-session-1", "Schema conversion failed!"
    assert metadata_dict["modality"] == "text", "Modality conversion failed!"
    
    print("✓ Storage schema test passed!")
    print()


def test_transcript_processing():
    """Test transcript processing"""
    print("=" * 60)
    print("Test 4: Transcript Processing")
    print("=" * 60)
    
    processor = TranscriptProcessor()
    
    # Sample transcript data
    transcript_data = {
        "transcript": "Patient reports fever, cough, and chest pain. Blood pressure: 140/90 mmHg.",
        "is_final": True,
        "confidence": 0.95,
        "speaker": "doctor",
        "timestamp": "2025-11-06T18:00:00Z",
        "session_id": "test-session-1"
    }
    
    print("Original Transcript Data:")
    print(f"  Transcript: {transcript_data['transcript']}")
    print(f"  Session ID: {transcript_data['session_id']}")
    print()
    
    # Process transcript
    processed = processor.process_transcript(
        transcript_data,
        session_metadata={"patient_id": "P12345", "doctor_id": "D001"}
    )
    
    print("Processed Transcript:")
    print(f"  Transcript: {processed['transcript']}")
    print(f"  Medical Entities: {len(processed['medical_entities'])}")
    print(f"  Corrections: {len(processed['corrections'])}")
    print()
    
    # Format for storage
    storage_data = processor.format_for_storage(processed)
    
    print("Storage-Ready Data:")
    print(f"  Modality: {storage_data['modality']}")
    print(f"  Medical Terms: {len(storage_data['medical_terms'])}")
    print(f"  Medical Entities: {len(storage_data['medical_entities'])}")
    print()
    
    assert storage_data["modality"] == "text", "Storage format incorrect!"
    assert len(storage_data["medical_entities"]) > 0, "No medical entities extracted!"
    
    print("✓ Transcript processing test passed!")
    print()


def test_storage_without_qdrant():
    """Test storage initialization without Qdrant"""
    print("=" * 60)
    print("Test 5: Storage Initialization (Without Qdrant)")
    print("=" * 60)
    
    try:
        from src.storage import QdrantStorage
        
        # Try to initialize (will fail if Qdrant not running, but that's OK)
        try:
            storage = QdrantStorage(
                host="localhost",
                port=6333,
                enable_encryption=True,
                enable_deidentification=True
            )
            
            info = storage.get_collection_info()
            print("✓ Qdrant storage initialized successfully!")
            print(f"  Collection: {info.get('name', 'N/A')}")
            print(f"  Points: {info.get('points_count', 'N/A')}")
            print()
            
        except Exception as e:
            print(f"⚠️  Qdrant not available: {e}")
            print("  This is expected if Qdrant is not running.")
            print("  To test with Qdrant:")
            print("    1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
            print("    2. Run this test again")
            print()
    
    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("  Install missing dependencies: pip install qdrant-client cryptography")
        print()


def main():
    """Run all quick tests"""
    print()
    print("=" * 60)
    print("Quick Storage Integration Tests")
    print("=" * 60)
    print()
    print("These tests don't require Qdrant to be running.")
    print("They test encryption, de-identification, schema, and processing.")
    print()
    
    try:
        test_encryption()
        test_deidentification()
        test_storage_schema()
        test_transcript_processing()
        test_storage_without_qdrant()
        
        print("=" * 60)
        print("✅ All quick tests completed!")
        print("=" * 60)
        print()
        print("To test with Qdrant:")
        print("  1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("  2. Run: python examples/test_storage_integration.py")
        print()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

