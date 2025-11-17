# Qdrant Isolation Strategy for HygiaAI

## Overview

This document describes how HygiaAI ensures Qdrant database isolation from other projects.

## Current Configuration

### Collection Naming Strategy
- **Prefix**: All collections use `hygiaai_` prefix
- **Default Collection**: `hygiaai_transcripts`
- **Purpose**: Ensures no naming conflicts with other projects

### Connection Settings
- **Default Host**: `localhost`
- **Default Port**: `6333` (standard Qdrant port)
- **Configurable via**: Environment variables `QDRANT_HOST` and `QDRANT_PORT`

### Vector Configuration
- **Default Vector Size**: `768` (BioBERT embeddings)
- **Distance Metric**: `COSINE`
- **Supports**: Multimodal embeddings (text, image, audio)

## Isolation Mechanisms

### 1. Collection Namespace
All HygiaAI collections are prefixed with `hygiaai_`:
- `hygiaai_transcripts` - Main transcript storage
- `hygiaai_knowledge_base` - Knowledge base documents
- `hygiaai_cases` - Clinical cases

This ensures that even if multiple projects share a Qdrant instance, collections won't conflict.

### 2. Environment-Based Configuration
Qdrant connection can be configured via environment variables:
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 3. Project-Specific Collection Names
The `QdrantStorage` class allows custom collection names:
```python
storage = QdrantStorage(
    collection_name="hygiaai_transcripts",  # Project-specific
    host="localhost",
    port=6333
)
```

## Recommendations for Better Isolation

### Option 1: Dedicated Qdrant Instance (Recommended)
Run a separate Qdrant instance for this project:
```bash
docker run -d \
  --name hygiaai-qdrant \
  -p 6334:6333 \
  -v hygiaai-qdrant-data:/qdrant/storage \
  qdrant/qdrant
```

Then set in `.env`:
```bash
QDRANT_PORT=6334
```

### Option 2: Qdrant Cloud
Use Qdrant Cloud for production (completely isolated):
- Sign up at https://cloud.qdrant.io
- Get your cluster URL and API key
- Set `QDRANT_HOST` to your cluster URL

### Option 3: Local Docker with Custom Port
Use Docker with a custom port mapping:
```bash
docker run -d \
  --name hygiaai-qdrant \
  -p 6334:6333 \
  qdrant/qdrant
```

## Verification

Run the isolation check script:
```bash
python examples/check_qdrant_isolation.py
```

This will:
1. Check if Qdrant is accessible
2. List all collections and identify which belong to HygiaAI
3. Warn if other projects' collections are found
4. Provide recommendations for better isolation

## Current Status

✅ **Isolation Strategy Implemented**:
- Collection names use `hygiaai_` prefix
- Configuration is environment-based
- No hardcoded collection names that could conflict

⚠️ **Potential Improvements**:
- Use a dedicated Qdrant instance (different port or Docker container)
- Set explicit `QDRANT_HOST` and `QDRANT_PORT` in `.env`
- Consider Qdrant Cloud for production

## Code References

- **Storage Module**: `src/storage/qdrant_storage.py`
- **Default Collection**: `"hygiaai_transcripts"` (line 67)
- **Configuration**: Environment variables `QDRANT_HOST`, `QDRANT_PORT` (lines 90-91)

## Testing

To test isolation:
1. Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
2. Run check: `python examples/check_qdrant_isolation.py`
3. Verify only HygiaAI collections exist

