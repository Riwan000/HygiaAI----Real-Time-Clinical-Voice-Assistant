# Multi-Collection Architecture Setup Guide

## Overview

HygiaAI uses separate Qdrant collections for different data types to ensure clean separation and optimal performance.

## Collections

1. **`clinical_kb_collection`** - Knowledge base (NCBI, PubMed, WHO, user uploads)
2. **`patient_memory_collection`** - Historical patient records (MIMIC, eICU)
3. **`hygiaai_cases`** - Real-time patient cases from HygiaAI users
4. **`imaging_collection`** - Medical images (optional)
5. **`audio_collection`** - Audio datasets (optional)

## Quick Start

### Step 1: Download Datasets

```bash
# Set PhysioNet credentials (optional, for MIMIC/eICU)
export PN_USERNAME="your_email"
export PN_PASSWORD="your_password"

# Download all datasets
python scripts/download_hygiaai_datasets.py
```

This will download:
- Knowledge base: NCBI Bookshelf, PubMed OA, WHO GHO
- Patient records: MIMIC-III, MIMIC-IV, eICU (if credentials provided)
- Imaging: MIMIC-CXR metadata
- Audio: OpenSLR

### Step 2: Ingest Knowledge Base

```bash
python scripts/ingest_knowledge_base.py
```

This populates `clinical_kb_collection` with:
- NCBI Bookshelf PDFs
- PubMed OA articles
- WHO Global Health data

### Step 3: Ingest Patient Records (Optional)

```bash
python scripts/ingest_patient_records.py
```

This populates `patient_memory_collection` with:
- MIMIC-III clinical notes
- MIMIC-IV clinical notes
- eICU patient data

**Note**: Requires PhysioNet credentials and downloaded datasets.

### Step 4: Verify Collections

Check your Qdrant dashboard or use:

```python
from src.storage.qdrant_storage import QdrantStorage

# Check knowledge base collection
kb_storage = QdrantStorage(collection_name="clinical_kb_collection")
info = kb_storage.get_collection_info()
print(f"Knowledge Base: {info.get('points_count', 0)} points")

# Check patient records collection
patient_storage = QdrantStorage(collection_name="patient_memory_collection")
info = patient_storage.get_collection_info()
print(f"Patient Records: {info.get('points_count', 0)} points")
```

## Collection Usage

### Knowledge Base Queries

```python
# Search knowledge base
kb_storage = get_qdrant_storage(collection_name="clinical_kb_collection")
results = kb_storage.search_with_filters(
    query_embedding=embedding,
    filters={"domain": "guidelines"},
    limit=10
)
```

### Patient Records Queries

```python
# Search patient records
patient_storage = get_qdrant_storage(collection_name="patient_memory_collection")
results = patient_storage.search_with_filters(
    query_embedding=embedding,
    filters={"modality": "text"},
    limit=10
)
```

### RAG Pipeline (Combined)

```python
# 1. Get knowledge base context
kb_results = kb_storage.search(query_embedding, limit=5)

# 2. Get similar patient cases
patient_results = patient_storage.search(query_embedding, limit=5)

# 3. Combine for RAG
rag_context = combine_for_rag(kb_results, patient_results)
```

## Migration from Single Collection

If you have existing data in `hygiaai_knowledge_base`:

1. **Backup existing data** (optional)
2. **Run ingestion scripts** to populate new collections
3. **Update code** to use new collection names (already done)
4. **Test** that everything works
5. **Keep old collection** as backup or delete after verification

## Important Notes

- ✅ **Knowledge base** goes to `clinical_kb_collection`
- ✅ **Patient records** go to `patient_memory_collection`
- ✅ **Real-time cases** stay in `hygiaai_cases`
- ❌ **Never mix** knowledge base and patient data in same collection
- ❌ **Don't use** `hygiaai_knowledge_base` for new uploads (use `clinical_kb_collection`)

## Troubleshooting

### Collection Not Found

If you get "collection not found" errors:
- Collections are created automatically when you ingest data
- Run the ingestion scripts to create collections
- Check Qdrant connection settings

### Empty Search Results

- Verify data was ingested successfully
- Check collection names match
- Verify embeddings are generated correctly

### Performance Issues

- Use appropriate collection for query type
- Limit search results
- Use filters to narrow results
- Consider collection size optimization

