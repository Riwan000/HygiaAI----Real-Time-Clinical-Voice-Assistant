# HygiaAI Quick Start Guide

This guide will help you set up and run the complete HygiaAI clinical voice assistant demo.

## Prerequisites

1. **Python 3.8+** installed
2. **Docker** installed (for Qdrant)
3. **Git** (if cloning the repository)

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Deepgram API (for transcription)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# LLM API Keys (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Ollama (optional, for local fallback)
OLLAMA_BASE_URL=http://localhost:11434/v1

# Qdrant (optional, defaults shown)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

**Note:** For the demo, you can skip API keys if you just want to see the core pipeline. Qdrant is required for storage/retrieval/visualization.

## Step 3: Start Qdrant Server

### Option A: Using Docker (Recommended)

```bash
# Start Qdrant in Docker
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Verify it's running
curl http://localhost:6333/health
```

### Option B: Using Docker Compose

Create a `docker-compose.yml` file:

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

### Option C: Native Installation

See [Qdrant Installation Guide](https://qdrant.tech/documentation/guides/installation/)

## Step 4: Run the End-to-End Demo

```bash
python examples/demo_end_to_end.py
```

## Expected Output

When everything is set up correctly, you should see:

### ✓ Step 1: Transcription Processing
- Processed transcript with medical terminology validation
- Extracted medical entities (symptoms, diagnoses, medications, vital signs)
- Spell-checking and terminology corrections

### ✓ Step 2: Entity Extraction
- Total entities extracted
- Entity summary by type
- Confidence scores for each entity

### ✓ Step 3: Embedding Generation
- 768-dimensional BioBERT embedding generated
- Ready for vector storage

### ✓ Step 4: Qdrant Storage
- Transcript stored successfully
- Case ID generated
- Additional demo cases stored for retrieval

### ✓ Step 5: Case Retrieval
- Retrieved similar cases
- Similarity scores
- Case metadata (diagnosis, outcome)

### ✓ Step 6: RAG-Based Clinical Insights
- Differential diagnoses with confidence scores
- Clinical recommendations with citations
- Summary and reasoning chain

### ✓ Step 7: Visualization Data
- Temporal trends analyzed
- Outbreak signals detected
- Case map generated with clustering

## Troubleshooting

### Qdrant Connection Error

**Error:** `[WinError 10061] No connection could be made because the target machine actively refused it`

**Solution:**
1. Make sure Docker is running
2. Start Qdrant: `docker run -d -p 6333:6333 qdrant/qdrant`
3. Verify: `curl http://localhost:6333/health` (should return `{"status":"ok"}`)

### LLM API Key Missing

**Error:** `OPENAI_API_KEY environment variable required`

**Solution:**
1. Add API key to `.env` file
2. Or use Ollama (local, no API key needed):
   - Install Ollama: https://ollama.ai
   - Run: `ollama pull llama3.1:latest`
   - The demo will automatically use Ollama as fallback

### Embedding Generation Error

**Error:** `ModuleNotFoundError: No module named 'transformers'`

**Solution:**
```bash
pip install transformers torch sentence-transformers
```

### PyTorch Installation (CPU)

```bash
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## Testing Individual Components

### Test Transcription Only
```bash
python examples/test_medical_entity_extraction_task2.py
```

### Test Embeddings Only
```bash
python examples/test_embeddings_task3.py
```

### Test Storage Only
```bash
python examples/test_storage_integration.py
```

### Test Retrieval Only
```bash
python examples/test_case_retrieval.py
```

## Running Unit Tests

```bash
# Run all tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_clinical_rag.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

## Next Steps

1. **Task 8:** Outbreak Detection Algorithm (quick, already partially implemented)
2. **Task 9:** HL7/FHIR EHR Integration (major integration)
3. **Task 10:** Privacy Compliance Implementation (mostly done, may need audit logging)
4. **Tasks 11-15:** Open-Access Knowledge Integration (separate pipeline)

## Architecture Overview

```
Patient Input → ASR Transcription (Deepgram)
      ↓
Entity Extraction → Medical Entities, Symptoms, Diagnosis
      ↓
Embedding Generation (BioBERT for text, CLIP for images)
      ↓
Qdrant Vector Store
  ↳ Multi-Vector per Case (Text + Image + Audio)
  ↳ Payload Filters (age, region, timestamp, comorbidity)
  ↳ Hybrid Search + Clustering
      ↓
Contextual Retrieval → Top Similar Cases
      ↓
RAG-Based Summary → Clinical Insight Report
      ↓
Visualization Layer → Temporal Trends + Similar Case Map
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test files in `examples/` directory
3. Check the PRD in `prd/hygiaai_qdrant_prd_combined.md`

