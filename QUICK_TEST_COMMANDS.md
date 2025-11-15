# Quick Test Commands for HygiaAI Storage

## 🚀 Quick Start Testing (No Qdrant Required)

### Test 1: Quick Storage Tests (No Qdrant)
Tests encryption, de-identification, schema, and processing without Qdrant:
```bash
python test_storage_quick.py
```

### Test 2: Unit Tests (Mocked Qdrant)
Tests with mocked Qdrant (no actual Qdrant needed):
```bash
python -m pytest tests/unit/test_qdrant_storage.py -v
```

### Test 3: All Unit Tests
Run all unit tests:
```bash
python -m pytest tests/unit/ -v
```

## 🔧 Testing With Qdrant Running

### Step 1: Start Qdrant

**Option A: Docker (Recommended)**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

**Option B: Docker Compose**
Create `docker-compose.yml`:
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

Then:
```bash
docker-compose up -d
```

**Verify Qdrant is Running:**
```bash
curl http://localhost:6333/health
# Should return: {"status":"ok"}
```

### Step 2: Run Integration Tests

```bash
# Full storage integration test
python examples/test_storage_integration.py

# Test specific components
python examples/test_medical_entity_extraction.py
python examples/test_error_handling.py
python examples/test_streaming_config.py
```

## 📋 Test Individual Components

### Test Encryption Only
```python
from src.storage import EncryptionManager

manager = EncryptionManager()
original = "Patient has fever"
encrypted = manager.encrypt(original)
decrypted = manager.decrypt(encrypted)
print(f"Original: {original}")
print(f"Decrypted: {decrypted}")
assert decrypted == original
```

### Test De-Identification Only
```python
from src.storage import DeIdentificationManager

manager = DeIdentificationManager()
text = "Patient email: john@example.com, phone: 555-123-4567"
deidentified = manager.deidentify_text(text)
print(f"De-identified: {deidentified}")
```

### Test Storage Schema
```python
from src.storage import StorageMetadata, ModalityType

metadata = StorageMetadata(
    session_id="test-1",
    patient_id="P12345",
    modality=ModalityType.TEXT
)
print(metadata.to_dict())
```

## 🧪 Test Full Integration Flow

Create `test_full_flow.py`:
```python
from src.transcription.transcript_processor import TranscriptProcessor
from src.storage import TranscriptStorage
import numpy as np

# Initialize
processor = TranscriptProcessor()
storage = TranscriptStorage()

# Process transcript
transcript_data = {
    "transcript": "Patient reports fever and cough",
    "session_id": "test-1",
    "confidence": 0.95
}
processed = processor.process_transcript(transcript_data)
storage_data = processor.format_for_storage(processed)

# Store (with dummy embedding)
embedding = np.random.rand(384).tolist()
point_id = storage.store(storage_data, embedding)
print(f"Stored: {point_id}")

# Retrieve
retrieved = storage.get(point_id)
print(f"Retrieved: {retrieved['transcript']}")

# Search
similar = storage.search("fever", limit=5)
print(f"Found {len(similar)} similar transcripts")
```

Run:
```bash
python test_full_flow.py
```

## 📊 Test Coverage Report

```bash
# Generate coverage report
python -m pytest tests/unit/ --cov=src/storage --cov-report=html

# View report
# Open htmlcov/index.html in browser
```

## ✅ Expected Test Results

### Quick Tests (No Qdrant)
- ✅ Encryption/Decryption: PASS
- ✅ De-Identification: PASS
- ✅ Storage Schema: PASS
- ✅ Transcript Processing: PASS
- ⚠️ Storage Operations: SKIP (Qdrant not running)

### Unit Tests (Mocked)
- ✅ 9/9 tests passing
- ✅ EncryptionManager tests
- ✅ DeIdentificationManager tests
- ✅ QdrantStorage tests (mocked)

### Integration Tests (With Qdrant)
- ✅ All quick tests: PASS
- ✅ Storage operations: PASS
- ✅ Similarity search: PASS

## 🔍 Troubleshooting

### Issue: "Qdrant not available"
**Solution:** Start Qdrant using Docker:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: "ModuleNotFoundError: No module named 'qdrant_client'"
**Solution:** Install dependencies:
```bash
pip install qdrant-client cryptography
```

### Issue: "ModuleNotFoundError: No module named 'cryptography'"
**Solution:** Install cryptography:
```bash
pip install cryptography
```

## 📝 Test Checklist

- [ ] Run quick tests: `python test_storage_quick.py`
- [ ] Run unit tests: `python -m pytest tests/unit/test_qdrant_storage.py -v`
- [ ] Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] Run integration tests: `python examples/test_storage_integration.py`
- [ ] Test encryption: Verify encrypt/decrypt works
- [ ] Test de-identification: Verify PHI is removed
- [ ] Test storage: Store and retrieve a transcript
- [ ] Test search: Search for similar transcripts

## 🎯 Next Steps

1. **Set up Qdrant** (if not already running)
2. **Run quick tests** to verify basic functionality
3. **Run unit tests** to verify all components
4. **Run integration tests** with Qdrant running
5. **Test with real embeddings** (when embedding model is integrated)

