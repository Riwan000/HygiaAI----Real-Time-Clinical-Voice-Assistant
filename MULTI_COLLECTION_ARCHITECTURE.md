# Multi-Collection Architecture for HygiaAI

## Overview

HygiaAI uses a **multi-collection architecture** in Qdrant to maintain clean separation between different data types. This prevents contamination, enables faster queries, and allows proper filtering.

## Collection Structure

### 1. `clinical_kb_collection` - Knowledge Base
**Purpose**: Medical knowledge, guidelines, textbooks, research articles

**Content**:
- NCBI Bookshelf medical textbooks
- PubMed Central Open Access articles
- WHO Global Health Observatory data
- Medical ontologies
- Clinical guidelines
- Treatment protocols

**Use Cases**:
- RAG-based clinical insights
- Knowledge retrieval for SOAP generation
- Clinical decision support
- Evidence-based recommendations

**Characteristics**:
- Public/open-access content
- No patient identifiers
- Structured medical knowledge
- Searchable by domain, source, year

---

### 2. `patient_memory_collection` - Patient Records
**Purpose**: De-identified patient clinical notes and records

**Content**:
- MIMIC-III clinical notes
- MIMIC-IV clinical notes
- eICU patient data
- AmsterdamUMCdb records
- i2b2 clinical notes
- Real patient consultations (from HygiaAI)

**Use Cases**:
- Similar case recall
- Pattern analysis
- Clinical trend identification
- Patient history retrieval

**Characteristics**:
- De-identified patient data
- HIPAA-compliant storage
- Encrypted sensitive fields (optional)
- Searchable by patient ID (hashed), date, modality

---

### 3. `imaging_collection` - Medical Imaging (Optional)
**Purpose**: Chest X-rays, medical images with metadata

**Content**:
- MIMIC-CXR images and reports
- CheXpert dataset
- NIH ChestXray14
- VinDr-PCXR

**Use Cases**:
- Image similarity search
- Radiology report generation
- Image classification

**Characteristics**:
- Image embeddings (CLIP or medical vision models)
- Text embeddings from radiology reports
- Multi-modal search capability

---

### 4. `audio_collection` - Audio Datasets (Optional)
**Purpose**: Medical speech recordings and transcripts

**Content**:
- OpenSLR medical speech dataset
- Clinical consultation audio
- Medical dictation samples

**Use Cases**:
- Speech recognition training
- Audio similarity search
- Transcription quality improvement

**Characteristics**:
- Audio embeddings
- Transcript embeddings
- Speaker diarization metadata

---

## Why Separate Collections?

### ✅ Benefits

1. **Clean Recall**: No mixing of knowledge base content with patient records
2. **Faster Queries**: Smaller collections = faster search
3. **Proper Filtering**: Can filter by collection type
4. **Security**: Patient data isolated from public knowledge
5. **Scalability**: Can scale collections independently
6. **Compliance**: Easier to manage HIPAA requirements for patient data

### ❌ Problems with Single Collection

- Knowledge base articles mixed with patient notes
- Slower queries (larger collection)
- Harder to filter by data type
- Security concerns (patient data exposure)
- Compliance issues

---

## Collection Configuration

### Knowledge Base Collection
```python
knowledge_storage = QdrantStorage(
    collection_name="clinical_kb_collection",
    vector_size=768,  # Text embeddings
    enable_encryption=False,  # Public data
    enable_deidentification=False  # No patient data
)
```

### Patient Records Collection
```python
patient_storage = QdrantStorage(
    collection_name="patient_memory_collection",
    vector_size=768,  # Text embeddings
    enable_encryption=True,  # Optional encryption
    enable_deidentification=True  # REQUIRED for patient data
)
```

### Imaging Collection (Optional)
```python
imaging_storage = QdrantStorage(
    collection_name="imaging_collection",
    vector_size=512,  # Image embeddings (CLIP)
    enable_encryption=False,
    enable_deidentification=True  # Patient images
)
```

---

## Usage Examples

### Query Knowledge Base
```python
# Search clinical guidelines
results = knowledge_storage.search_with_filters(
    query_embedding=query_embedding,
    filters={"domain": "guidelines", "source": "WHO"},
    limit=10
)
```

### Query Patient Records
```python
# Find similar patient cases
results = patient_storage.search_with_filters(
    query_embedding=query_embedding,
    filters={"modality": "text", "patient_id": hashed_id},
    limit=10
)
```

### RAG Pipeline
```python
# 1. Retrieve from knowledge base
kb_results = knowledge_storage.search(query_embedding, limit=5)

# 2. Retrieve similar patient cases
patient_results = patient_storage.search(query_embedding, limit=5)

# 3. Combine for RAG context
rag_context = combine_results(kb_results, patient_results)
```

---

## Data Ingestion Scripts

### 1. Download Datasets
```bash
python scripts/download_hygiaai_datasets.py
```

### 2. Ingest Knowledge Base
```bash
python scripts/ingest_knowledge_base.py
```
Populates: `clinical_kb_collection`

### 3. Ingest Patient Records
```bash
python scripts/ingest_patient_records.py
```
Populates: `patient_memory_collection`

### 4. Ingest Imaging Data (Optional)
```bash
python scripts/ingest_imaging_data.py
```
Populates: `imaging_collection`

### 5. Ingest Audio Data (Optional)
```bash
python scripts/ingest_audio_data.py
```
Populates: `audio_collection`

---

## Collection Naming Convention

- `clinical_kb_collection` - Knowledge base
- `patient_memory_collection` - Patient records
- `imaging_collection` - Medical images
- `audio_collection` - Audio datasets
- `hygiaai_cases` - Real-time HygiaAI cases (existing)
- `hygiaai_knowledge_base` - User-uploaded knowledge (existing)

---

## Migration from Single Collection

If you have existing data in a single collection:

1. **Export existing data**:
   ```python
   # Export by filtering
   kb_data = export_by_source(["NCBI", "PubMed", "WHO"])
   patient_data = export_by_source(["MIMIC", "eICU"])
   ```

2. **Create new collections**:
   ```python
   # Create collections
   create_collection("clinical_kb_collection")
   create_collection("patient_memory_collection")
   ```

3. **Ingest into new collections**:
   ```python
   # Ingest knowledge base
   ingest_to_collection(kb_data, "clinical_kb_collection")
   
   # Ingest patient records
   ingest_to_collection(patient_data, "patient_memory_collection")
   ```

4. **Update code** to use new collections

5. **Verify** data integrity

6. **Delete old collection** (after verification)

---

## Best Practices

1. ✅ **Always use separate collections** for different data types
2. ✅ **Enable de-identification** for patient data collections
3. ✅ **Use appropriate vector sizes** (768 for text, 512 for images)
4. ✅ **Filter by collection** when querying
5. ✅ **Monitor collection sizes** for performance
6. ✅ **Backup collections** separately
7. ❌ **Never mix** knowledge base and patient data
8. ❌ **Don't use** single collection for all data types

---

## Summary

| Collection | Content | Vector Size | De-ID | Encryption |
|------------|---------|-------------|-------|------------|
| `clinical_kb_collection` | Knowledge base | 768 | No | No |
| `patient_memory_collection` | Patient records | 768 | Yes | Optional |
| `imaging_collection` | Medical images | 512 | Yes | Optional |
| `audio_collection` | Audio datasets | 768 | Yes | Optional |

This architecture ensures:
- ✅ Clean data separation
- ✅ Fast queries
- ✅ Proper security
- ✅ HIPAA compliance
- ✅ Scalability

