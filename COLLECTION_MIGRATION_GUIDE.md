# Collection Migration Guide

## Current Status

✅ **Multi-collection architecture implemented**

## Collection Mapping

| Old Collection | New Collection | Purpose |
|----------------|----------------|---------|
| `hygiaai_knowledge_base` | `clinical_kb_collection` | Knowledge base (NCBI, PubMed, WHO, user uploads) |
| `hygiaai_cases` | `hygiaai_cases` | Real-time patient cases (unchanged) |
| N/A | `patient_memory_collection` | Historical patient records (MIMIC, eICU) |
| N/A | `imaging_collection` | Medical images (optional) |
| N/A | `audio_collection` | Audio datasets (optional) |

## What Changed

### 1. API Updates (`src/api/clinical_memory_api.py`)

- ✅ Updated `get_qdrant_storage()` to accept `collection_name` parameter
- ✅ Knowledge base endpoints now use `clinical_kb_collection`
- ✅ File upload endpoint uses `clinical_kb_collection`
- ✅ Search endpoints use `clinical_kb_collection`

### 2. New Scripts Created

- ✅ `scripts/download_hygiaai_datasets.py` - Download all datasets
- ✅ `scripts/ingest_knowledge_base.py` - Populate `clinical_kb_collection`
- ✅ `scripts/ingest_patient_records.py` - Populate `patient_memory_collection`

### 3. Documentation

- ✅ `MULTI_COLLECTION_ARCHITECTURE.md` - Architecture overview
- ✅ `scripts/README_MULTI_COLLECTION.md` - Setup guide

## Migration Steps

### Option 1: Fresh Start (Recommended)

1. **Download datasets**:
   ```bash
   python scripts/download_hygiaai_datasets.py
   ```

2. **Ingest knowledge base**:
   ```bash
   python scripts/ingest_knowledge_base.py
   ```

3. **Ingest patient records** (optional):
   ```bash
   python scripts/ingest_patient_records.py
   ```

4. **Verify collections**:
   - Check Qdrant dashboard
   - Test knowledge base search
   - Test patient record search

### Option 2: Migrate Existing Data

If you have existing data in `hygiaai_knowledge_base`:

1. **Export existing data**:
   ```python
   from src.storage.qdrant_storage import QdrantStorage
   
   old_storage = QdrantStorage(collection_name="hygiaai_knowledge_base")
   # Export all points
   scroll_result = old_storage.client.scroll(
       collection_name="hygiaai_knowledge_base",
       limit=10000,
       with_payload=True,
       with_vectors=True
   )
   ```

2. **Create new collection**:
   ```python
   new_storage = QdrantStorage(collection_name="clinical_kb_collection")
   # Collection created automatically on first use
   ```

3. **Re-ingest into new collection**:
   - Use the ingestion scripts
   - Or manually copy points

4. **Update code** (already done):
   - API endpoints updated
   - Collection names updated

5. **Test and verify**:
   - Test knowledge base search
   - Verify data integrity
   - Check performance

6. **Delete old collection** (after verification):
   ```python
   old_storage.client.delete_collection("hygiaai_knowledge_base")
   ```

## Backward Compatibility

The code now uses `clinical_kb_collection` by default. If you have existing data in `hygiaai_knowledge_base`:

1. **Option A**: Migrate data to new collection (recommended)
2. **Option B**: Keep both collections and update code to check both
3. **Option C**: Use `hygiaai_knowledge_base` as alias (not recommended)

## Testing

### Test Knowledge Base Search

```bash
curl -X POST http://localhost:8000/api/v1/clinical_memory/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hypertension treatment", "limit": 10}'
```

### Test File Upload

```bash
curl -X POST http://localhost:8000/api/v1/clinical_memory/knowledge/upload \
  -F "file=@medical_textbook.pdf" \
  -F "domain=guidelines" \
  -F "source=User Upload"
```

### Verify Collections

```python
from src.storage.qdrant_storage import QdrantStorage

# Check knowledge base
kb = QdrantStorage(collection_name="clinical_kb_collection")
info = kb.get_collection_info()
print(f"Knowledge Base: {info}")

# Check patient records
patient = QdrantStorage(collection_name="patient_memory_collection")
info = patient.get_collection_info()
print(f"Patient Records: {info}")
```

## Troubleshooting

### "Collection not found" Error

**Solution**: Run ingestion scripts to create collections:
```bash
python scripts/ingest_knowledge_base.py
```

### Empty Search Results

**Possible causes**:
1. Collection is empty - run ingestion scripts
2. Wrong collection name - verify collection name in code
3. Embedding mismatch - ensure vector_size matches (768)

**Solution**: Check collection info:
```python
storage = QdrantStorage(collection_name="clinical_kb_collection")
info = storage.get_collection_info()
print(f"Points: {info.get('points_count', 0)}")
```

### Data Not Appearing

**Check**:
1. Verify ingestion script completed successfully
2. Check Qdrant logs for errors
3. Verify collection name matches
4. Check if data was filtered out

## Next Steps

1. ✅ Download datasets
2. ✅ Ingest knowledge base
3. ✅ Ingest patient records (optional)
4. ✅ Test knowledge base search
5. ✅ Test file upload
6. ✅ Verify collections are separate
7. ✅ Update any custom code using old collection names

## Summary

- ✅ Multi-collection architecture implemented
- ✅ API updated to use `clinical_kb_collection`
- ✅ Download and ingestion scripts created
- ✅ Documentation created
- ✅ Backward compatibility considered

**Ready to use!** Run the ingestion scripts to populate your collections.

