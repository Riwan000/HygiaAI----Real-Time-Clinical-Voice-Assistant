# HygiaAI - Real-Time Clinical Voice Assistant

A comprehensive clinical voice assistant powered by Qdrant vector database, featuring real-time transcription, medical entity extraction, RAG-based clinical insights, and temporal trend visualization.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Deepgram API (for transcription)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# LLM API Keys (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama (optional, for local fallback)
OLLAMA_BASE_URL=http://localhost:11434/v1
```

### 3. Start Qdrant Server

**Windows (PowerShell):**
```powershell
.\examples\setup_qdrant.ps1
```

**Linux/Mac:**
```bash
chmod +x examples/setup_qdrant.sh
./examples/setup_qdrant.sh
```

**Or manually:**
```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 4. Run the Demo

```bash
python examples/demo_end_to_end.py
```

## 📋 Features

### ✅ Completed Features

#### Backend Features

1. **ASR Transcription (Deepgram)**
   - Real-time streaming transcription
   - Adaptive streaming configuration
   - Error handling and retry logic
   - Medical terminology accuracy

2. **Entity Extraction**
   - Medical Named Entity Recognition (NER)
   - Medical terminology validation
   - Spell-checking
   - Entity evaluation metrics

3. **Embedding Generation**
   - Text embeddings (BioBERT)
   - Image embeddings (CLIP)
   - Multimodal embeddings

4. **Qdrant Vector Store Integration**
   - Multi-vector embeddings (text + image)
   - Knowledge base documents
   - Advanced filtering (range, "in", exact match)
   - Hybrid search (semantic + keyword)
   - Knowledge ingestion pipeline

5. **Contextual Retrieval**
   - Semantic search
   - Keyword-based search
   - Hybrid search
   - Filtering by demographics, time range, entity types

6. **RAG-Based Clinical Insights**
   - Multi-provider LLM support (OpenAI, Anthropic, OpenRouter, Ollama)
   - Context-aware insight generation
   - Differential diagnoses
   - Clinical recommendations with citations
   - Ollama fallback support

7. **Visualization Layer**
   - Temporal trend analysis
   - Case map visualization
   - Outbreak detection
   - RESTful API endpoints

#### Frontend Features

8. **SOAP Note Viewer** ✅
   - Expand/collapse sections (S/O/A/P)
   - Patient and clinician information display
   - PDF export with professional formatting
   - Copy to clipboard and print functionality
   - Manual editing with version history
   - Annotations and comments support

9. **Analytics & Visualization Dashboard** ✅
   - Interactive time-series trend charts (Plotly.js)
   - Disease cluster bubble maps
   - Clinic-level disease pattern heatmaps
   - Outbreak alert notifications with severity levels
   - Comprehensive filter system (time range, region, disease type, granularity)
   - Chart export (PNG, SVG)
   - Real-time data updates

### 🚧 Pending Features

10. **Case Timeline Viewer** (in progress)
11. **Knowledge Base Browser UI**
12. **Multimodal Input UI** (partially implemented)
13. **Outbreak Detection Algorithm** (partially implemented)
14. **HL7/FHIR EHR Integration**
15. **Privacy Compliance Implementation** (mostly done)
16-20. **Open-Access Knowledge Integration**

## 📁 Project Structure

```
HygiaAI----Real-Time-Clinical-Voice-Assistant/
├── src/
│   ├── transcription/      # Deepgram ASR integration
│   ├── entity_extraction/  # Medical NER and validation
│   ├── embeddings/         # Text, image, multimodal embeddings
│   ├── storage/            # Qdrant storage and encryption
│   ├── retrieval/          # Case retrieval and search
│   ├── rag/                # RAG-based clinical insights
│   ├── visualization/      # Temporal trends and case maps
│   ├── models/             # Data models
│   └── api/                # FastAPI endpoints
├── tests/
│   └── unit/               # Unit tests
├── examples/               # Demo scripts
├── prd/                    # Product requirements
└── requirements.txt        # Python dependencies
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_clinical_rag.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

## 📊 Test Results

- **Total Tests:** 123
- **Passed:** 122
- **Skipped:** 1 (Anthropic - library not available)
- **Failed:** 0

## 🔧 Configuration

### Qdrant Configuration

Default settings:
- Host: `localhost`
- Port: `6333`
- Collection: `clinical_cases`
- Vector Size: `384` (BioBERT) or `512` (CLIP)

### LLM Configuration

Supported providers:
- **OpenAI:** GPT-4, GPT-3.5
- **Anthropic:** Claude 3 Opus, Sonnet
- **OpenRouter:** Multiple models
- **Ollama:** Local models (fallback)

Default model: `gpt-4` (OpenAI)

## 📖 Documentation

- **Quick Start Guide:** `QUICK_START_GUIDE.md`
- **PRD:** `prd/hygiaai_qdrant_prd_combined.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Frontend Demo Guide:** `docs/FRONTEND_DEMO_GUIDE.md`

## 🏗️ Architecture

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

## 🔐 Privacy & Compliance

- **Encryption:** End-to-end encryption for sensitive data
- **De-identification:** PHI removal and patient ID hashing
- **HIPAA Compliance:** Audit trails and access controls
- **On-premise Qdrant:** No cloud data leak

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Contact

[Add contact information here]
