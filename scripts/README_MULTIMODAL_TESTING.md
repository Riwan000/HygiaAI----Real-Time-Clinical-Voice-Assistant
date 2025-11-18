# Multimodal Input Testing Guide

This guide explains how to verify that the multimodal input feature is working correctly.

## Quick Test

Run the automated test script:

```bash
python scripts/test_multimodal_input.py
```

This script will:
1. ✅ Check if backend server is running
2. ✅ Test text-only input
3. ✅ Test file upload
4. ✅ Verify data storage in Qdrant
5. ✅ Check RAG suggestion generation
6. ✅ Verify collection updates

---

## Manual Testing Methods

### Method 1: Frontend Testing

1. **Start Backend Server:**
   ```bash
   python run_server.py
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Navigate to Multimodal Input Page:**
   - Open browser: `http://localhost:3000`
   - Go to "Multimodal Input" page

4. **Test Text Input:**
   - Enter patient ID (e.g., `TEST001`)
   - Paste clinical transcript in text area
   - Fill in metadata (age group, region, comorbidities, diagnosis)
   - Click "Submit"
   - **Expected:** Success message, RAG suggestions displayed

5. **Test File Upload:**
   - Select a text file (`.txt`, `.md`) or audio file
   - Fill in patient metadata
   - Click "Submit"
   - **Expected:** File uploads, processes, shows RAG suggestions

6. **Verify Results:**
   - Check for success message
   - Verify RAG suggestions appear (differential diagnoses, recommendations, summary)
   - Check browser console for errors

---

### Method 2: API Testing with cURL

**Test Text Input:**
```bash
curl -X POST "http://localhost:8000/api/v1/clinical_memory/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "patient_id=TEST001" \
  -F "transcript_text=Patient presents with cough and fever for 3 days. History of hypertension." \
  -F "age_group=adult" \
  -F "region=urban" \
  -F "comorbidities=[\"hypertension\"]" \
  -F "diagnosis=Pneumonia, suspected"
```

**Test File Upload:**
```bash
curl -X POST "http://localhost:8000/api/v1/clinical_memory/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "patient_id=TEST002" \
  -F "text_file=@/path/to/clinical_note.txt" \
  -F "age_group=adult" \
  -F "region=urban" \
  -F "diagnosis=Acute bronchitis"
```

---

### Method 3: Python Script Testing

Use the provided test script:

```bash
# Run all tests
python scripts/test_multimodal_input.py

# Or use Python requests directly
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/clinical_memory/ingest',
    data={
        'patient_id': 'TEST003',
        'transcript_text': 'Patient complaint: chest pain',
        'age_group': 'adult'
    }
)
print(response.json())
"
```

---

## What to Check

### ✅ Success Indicators

1. **API Response:**
   - Status code: `200 OK`
   - Response includes `case_id`
   - `status: "success"`
   - `modalities_processed` includes your input type
   - `rag_suggestions` object is present

2. **RAG Suggestions:**
   - `summary` field contains clinical summary
   - `differential_diagnoses` array has entries
   - `recommendations` array has entries
   - `confidence_score` is present

3. **Qdrant Storage:**
   - `patient_memory_collection` point count increases
   - `hygiaai_cases` point count increases
   - `clinical_kb_collection` increases (if summary generated)

4. **Backend Logs:**
   - `✓ Stored patient record in patient_memory_collection`
   - `✓ RAG suggestions generated successfully`
   - `✓ Stored patient summary in knowledge base`

---

## Verification Steps

### Step 1: Check Collection Counts Before

```bash
python scripts/check_qdrant_status.py
```

Note the point counts for:
- `patient_memory_collection`
- `hygiaai_cases`
- `clinical_kb_collection`

### Step 2: Submit Multimodal Input

Via frontend or API

### Step 3: Check Collection Counts After

```bash
python scripts/check_qdrant_status.py
```

**Expected Changes:**
- `patient_memory_collection`: +1 or more
- `hygiaai_cases`: +1 or more
- `clinical_kb_collection`: +1 or more (if summary generated)

### Step 4: Verify Stored Data

```bash
python scripts/test_multimodal_input.py
```

Check the verification section to see stored patient records.

---

## Troubleshooting

### Issue: API Returns 500 Error

**Check:**
1. Backend server is running
2. Qdrant connection is configured correctly
3. Environment variables are set (`QDRANT_URL`, `QDRANT_API_KEY`, `GOOGLE_API_KEY`)
4. Backend logs for error details

**Solution:**
```bash
# Check backend logs
# Look for error messages

# Verify environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('QDRANT_URL:', os.getenv('QDRANT_URL')); print('GOOGLE_API_KEY:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')"
```

### Issue: No RAG Suggestions

**Check:**
1. `GOOGLE_API_KEY` is set and valid
2. Gemini API is accessible
3. Backend logs for RAG generation errors

**Solution:**
```bash
# Test Gemini API
python test_gemini.py

# Check API key
echo $GOOGLE_API_KEY  # Should show your API key
```

### Issue: Data Not Stored in Qdrant

**Check:**
1. Qdrant connection is working
2. Collection exists (created automatically)
3. Backend logs for storage errors

**Solution:**
```bash
# Test Qdrant connection
python test_qdrant_connection.py

# Check collection status
python scripts/check_qdrant_status.py
```

### Issue: Frontend Shows Error

**Check:**
1. Browser console for errors
2. Network tab for API request/response
3. Backend server is running
4. CORS is configured correctly

**Solution:**
- Check browser console (F12)
- Verify API endpoint URL in network tab
- Check backend CORS configuration

---

## Expected Behavior

### When Submitting Text Input:

1. **Request sent** → Backend receives data
2. **Case created** → Case ID generated
3. **Data processed** → Text extracted, entities identified
4. **Stored in Qdrant** → 
   - `hygiaai_cases` collection
   - `patient_memory_collection` collection
5. **RAG generated** → 
   - Clinical insights generated
   - Summary created
   - Differential diagnoses suggested
   - Recommendations provided
6. **Summary stored** → 
   - Stored in `clinical_kb_collection`
7. **Response returned** → 
   - Case ID
   - RAG suggestions
   - Status

### When Submitting File Upload:

Same as above, plus:
- File is read and processed
- Content extracted from file
- File content used for RAG generation

---

## Monitoring Real-Time Updates

Use the monitor script while testing:

```bash
# Terminal 1: Start monitor
python scripts/monitor_qdrant_updates.py

# Terminal 2: Submit multimodal input
# (via frontend or API)

# Watch Terminal 1 for real-time updates
```

You should see:
```
🟢 [14:23:45] patient_memory_collection: +1 points (Total: 1,240)
🟢 [14:23:45] hygiaai_cases: +1 points (Total: 457)
🟢 [14:23:46] clinical_kb_collection: +3 points (Total: 1,240)
```

---

## Quick Checklist

- [ ] Backend server is running
- [ ] Frontend is running (for UI testing)
- [ ] Qdrant is accessible
- [ ] Google API key is configured
- [ ] Test script runs successfully
- [ ] Collection counts increase after submission
- [ ] RAG suggestions are generated
- [ ] Patient data appears in `patient_memory_collection`
- [ ] Summary appears in `clinical_kb_collection`

---

## Additional Resources

- **Check Qdrant Status:** `python scripts/check_qdrant_status.py`
- **Monitor Updates:** `python scripts/monitor_qdrant_updates.py`
- **Test Qdrant Connection:** `python test_qdrant_connection.py`
- **Test Gemini API:** `python test_gemini.py`

