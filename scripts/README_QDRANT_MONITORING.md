# Qdrant Database Monitoring Guide

This guide explains how to verify that your Qdrant database is being updated correctly.

## Methods to Check Qdrant Updates

### 1. **Quick Status Check Script** (Recommended)

Run the status checker script to see current collection information:

```bash
python scripts/check_qdrant_status.py
```

**Output includes:**
- Total point counts for each collection
- Recent entries (last 10)
- Collection availability status
- Connection information

**Example output:**
```
================================================================================
Collection: clinical_kb_collection
================================================================================
✓ Connected to Qdrant Cloud: https://your-cluster.qdrant.io

📊 Collection Statistics:
  - Total Points: 1,234
  - Vectors: 1,234

📝 Recent Entries (Last 10):
  1. ID: abc123
     Title: Patient Summary - PATIENT001 - case_20240101...
     Source: HygiaAI Patient Summary | Domain: guidelines
```

---

### 2. **Real-Time Monitoring Script**

Monitor collections for updates in real-time:

```bash
python scripts/monitor_qdrant_updates.py
```

**Options:**
```bash
# Check every 5 seconds (default)
python scripts/monitor_qdrant_updates.py

# Check every 10 seconds
python scripts/monitor_qdrant_updates.py --interval 10
```

**What it shows:**
- Initial baseline counts
- Real-time updates when points are added/removed
- Timestamp of each update
- Current status every 30 seconds

**Example output:**
```
🟢 [14:23:45] patient_memory_collection: +5 points (Total: 1,239)
🟢 [14:23:50] clinical_kb_collection: +3 points (Total: 1,237)
⏱️  [14:24:00] Status: clinical_kb_collection: 1,237 | patient_memory_collection: 1,239 | hygiaai_cases: 456
```

---

### 3. **Qdrant Dashboard** (If Available)

If you're using Qdrant Cloud or have the dashboard enabled:

1. **Qdrant Cloud Dashboard:**
   - Log in to https://cloud.qdrant.io
   - Navigate to your cluster
   - View collections and point counts
   - See real-time statistics

2. **Local Qdrant Dashboard:**
   - If running locally, dashboard is usually at: `http://localhost:6333/dashboard`
   - View collections, points, and search functionality

---

### 4. **API Endpoint** (Coming Soon)

We'll add a `/api/v1/clinical_memory/status` endpoint to check collection status via API.

---

## Collections to Monitor

### `clinical_kb_collection`
- **Purpose**: Medical knowledge base (NCBI, PubMed, WHO, user uploads, patient summaries)
- **Updates when**: 
  - Knowledge base files are uploaded
  - Patient summaries are generated
  - Scripts ingest medical textbooks/articles

### `patient_memory_collection`
- **Purpose**: Patient clinical records and history
- **Updates when**:
  - Patient data is uploaded via multimodal ingestion
  - Patient consultations are stored
  - Historical datasets are ingested

### `hygiaai_cases`
- **Purpose**: Real-time patient cases from HygiaAI users
- **Updates when**:
  - Cases are ingested via API
  - SOAP notes are generated
  - Clinical data is processed

---

## Verification Workflow

### After Uploading Patient Data:

1. **Before upload:**
   ```bash
   python scripts/check_qdrant_status.py
   ```
   Note the point counts

2. **Upload patient data** via the frontend or API

3. **After upload:**
   ```bash
   python scripts/check_qdrant_status.py
   ```
   Compare point counts - should increase

4. **Check recent entries** to verify your data was stored

### After Uploading Knowledge Base Files:

1. **Check initial status:**
   ```bash
   python scripts/check_qdrant_status.py
   ```

2. **Upload file** via Knowledge Browser in frontend

3. **Monitor in real-time:**
   ```bash
   python scripts/monitor_qdrant_updates.py
   ```
   Watch for updates to `clinical_kb_collection`

4. **Verify:**
   ```bash
   python scripts/check_qdrant_status.py
   ```
   Check that new entries appear in recent entries

---

## Troubleshooting

### No Updates Detected

1. **Check Qdrant connection:**
   ```bash
   python scripts/check_qdrant_status.py
   ```
   Look for connection errors

2. **Verify environment variables:**
   - `QDRANT_URL` (for cloud) or `QDRANT_HOST`/`QDRANT_PORT` (for local)
   - `QDRANT_API_KEY` (if using cloud)

3. **Check backend logs:**
   - Look for "✓ Stored patient record" messages
   - Look for "✓ Stored patient summary in knowledge base" messages
   - Check for any error messages

4. **Verify collection exists:**
   - Collections are created automatically on first use
   - If missing, run ingestion scripts to create them

### Collection Not Found

If a collection doesn't exist:
- Run the appropriate ingestion script:
  - `python scripts/populate_soap_disease_knowledge.py` (for knowledge base)
  - Upload a file via frontend (creates collection automatically)
  - Upload patient data (creates collection automatically)

---

## Quick Reference

| Task | Command |
|------|---------|
| Check current status | `python scripts/check_qdrant_status.py` |
| Monitor updates | `python scripts/monitor_qdrant_updates.py` |
| Monitor with custom interval | `python scripts/monitor_qdrant_updates.py --interval 10` |

---

## Expected Behavior

### When Uploading Patient Data:
- `patient_memory_collection` should increase by 1+ points
- `hygiaai_cases` should increase by 1+ points
- `clinical_kb_collection` should increase if summary is generated

### When Uploading Knowledge Base Files:
- `clinical_kb_collection` should increase (multiple points per file due to chunking)

### When Generating SOAP Notes:
- Patient history is retrieved from `patient_memory_collection`
- Knowledge base context is retrieved from `clinical_kb_collection`
- New summaries are stored in `clinical_kb_collection`

---

## Tips

1. **Run status check before and after operations** to verify updates
2. **Use real-time monitoring** when testing uploads to see immediate results
3. **Check recent entries** to verify content is correct
4. **Monitor logs** for confirmation messages from the backend
5. **Compare point counts** over time to track growth

