# Testing Guide for HygiaAI Storage Integration

This guide explains how to test the transcript storage and retrieval functionality.

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**
   Create a `.env` file in the project root:
   ```env
   DEEPGRAM_API_KEY=your_deepgram_api_key
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ENCRYPTION_KEY=your_encryption_key_here  # Optional, will be auto-generated if not provided
   ```

## Testing Options

### Option 1: Test Without Qdrant (Unit Tests)

These tests use mocks and don't require Qdrant to be running:

```bash
# Run all storage unit tests
python -m pytest tests/unit/test_qdrant_storage.py -v

# Run specific test classes
python -m pytest tests/unit/test_qdrant_storage.py::TestEncryptionManager -v
python -m pytest tests/unit/test_qdrant_storage.py::TestDeIdentificationManager -v
```

### Option 2: Test With Qdrant Running

#### Step 1: Start Qdrant

**Using Docker (Recommended):**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

**Using Docker Compose:**
Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

Then run:
```bash
docker-compose up -d
```

**Verify Qdrant is Running:**
```bash
curl http://localhost:6333/health
```

#### Step 2: Run Integration Tests

```bash
# Run the storage integration test script
python examples/test_storage_integration.py
```

### Option 3: Test Individual Components

#### Test Encryption Only

```python
from src.storage import EncryptionManager

# Initialize encryption manager
manager = EncryptionManager()

# Test encryption/decryption
original = "Patient has fever"
encrypted = manager.encrypt(original)
decrypted = manager.decrypt(encrypted)

print(f"Original: {original}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")
assert decrypted == original
print("✓ Encryption test passed!")
```

#### Test De-Identification Only

```python
from src.storage import DeIdentificationManager

# Initialize de-identification manager
manager = DeIdentificationManager()

# Test de-identification
text = "Patient email: john@example.com, phone: 555-123-4567"
deidentified = manager.deidentify_text(text)

print(f"Original: {text}")
print(f"De-identified: {deidentified}")
print("✓ De-identification test passed!")
```

#### Test Storage Schema

```python
from src.storage import StorageMetadata, ModalityType
from datetime import datetime, timezone

# Create metadata
metadata = StorageMetadata(
    session_id="test-session-1",
    patient_id="P12345",
    doctor_id="D001",
    modality=ModalityType.TEXT,
    confidence=0.95
)

# Convert to dict
metadata_dict = metadata.to_dict()
print(f"Metadata: {metadata_dict}")
print("✓ Schema test passed!")
```

### Option 4: Test Full Integration

Create a test script to test the complete flow:

```python
# test_full_integration.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transcription.transcript_processor import TranscriptProcessor
from src.storage import TranscriptStorage, QdrantStorage
import numpy as np

# Initialize components
processor = TranscriptProcessor()
storage = QdrantStorage(enable_encryption=True, enable_deidentification=True)

# Sample transcript data
transcript_data = {
    "transcript": "Patient reports fever, cough, and chest pain. Blood pressure: 140/90 mmHg.",
    "is_final": True,
    "confidence": 0.95,
    "speaker": "doctor",
    "timestamp": "2025-11-06T18:00:00Z",
    "session_id": "test-session-1"
}

# Process transcript
processed = processor.process_transcript(
    transcript_data,
    session_metadata={"patient_id": "P12345", "doctor_id": "D001"}
)

print("Processed Transcript:")
print(f"  Transcript: {processed['transcript']}")
print(f"  Medical Entities: {len(processed['medical_entities'])}")
print()

# Format for storage
storage_data = processor.format_for_storage(processed)

# Generate dummy embedding (replace with actual embedding model)
embedding = np.random.rand(384).tolist()

# Store in Qdrant
point_id = storage.store_transcript(storage_data, embedding)
print(f"✓ Stored transcript with ID: {point_id}")
print()

# Retrieve transcript
retrieved = storage.get_transcript(point_id)
if retrieved:
    print("Retrieved Transcript:")
    print(f"  ID: {retrieved['id']}")
    print(f"  Transcript: {retrieved['transcript'][:50]}...")
    print("✓ Retrieval test passed!")
print()

# Search for similar transcripts
query_embedding = np.random.rand(384).tolist()
similar = storage.search_similar(query_embedding, limit=5)
print(f"✓ Found {len(similar)} similar transcripts")
```

Run it:
```bash
python test_full_integration.py
```

## Test Coverage

### Unit Tests
- ✅ Encryption/Decryption
- ✅ De-Identification
- ✅ Storage Schema
- ✅ Qdrant Storage (mocked)

### Integration Tests
- ✅ Encryption/Decryption
- ✅ De-Identification
- ✅ Storage Schema
- ✅ Transcript Processing and Storage Integration
- ⚠️ Storage Operations (requires Qdrant running)

## Troubleshooting

### Qdrant Connection Issues

**Error: "No connection could be made because the target machine actively refused it"**
- Solution: Start Qdrant using Docker or ensure Qdrant is running on the specified host/port

**Error: "Collection not found"**
- Solution: The collection will be created automatically on first use. Ensure Qdrant is running.

### Encryption Issues

**Error: "Invalid key"**
- Solution: Ensure ENCRYPTION_KEY is a valid Fernet key (44 characters) or let it auto-generate

**Warning: "No ENCRYPTION_KEY found in environment"**
- This is normal. A key will be auto-generated. Store it securely for production use.

### Import Errors

**Error: "ModuleNotFoundError: No module named 'qdrant_client'"**
- Solution: `pip install qdrant-client`

**Error: "ModuleNotFoundError: No module named 'cryptography'"**
- Solution: `pip install cryptography`

## Quick Test Commands

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run storage tests only
python -m pytest tests/unit/test_qdrant_storage.py -v

# Run example scripts
python examples/test_storage_integration.py
python examples/test_medical_entity_extraction.py
python examples/test_error_handling.py
python examples/test_streaming_config.py

# Run with coverage
python -m pytest tests/unit/ --cov=src/storage --cov-report=html
```

## Next Steps

1. **Set up Qdrant** (if not already running)
2. **Run unit tests** to verify basic functionality
3. **Run integration tests** with Qdrant running
4. **Test with real embeddings** (when embedding model is integrated)

