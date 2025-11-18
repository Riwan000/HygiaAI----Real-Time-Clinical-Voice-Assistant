# Offline Rural Demo Guide

Complete guide for demonstrating HygiaAI in offline/rural environments without internet connectivity.

## 🎯 Overview

This guide shows you how to set up and demonstrate HygiaAI in environments with **no internet connection**, perfect for:
- Rural healthcare clinics
- Remote medical facilities
- Offline demonstrations
- Areas with unreliable connectivity

## ✅ What Works Offline

### Fully Functional Features:
- ✅ **Live Audio Transcription** (requires Deepgram API key - can be pre-configured)
- ✅ **Audio File Transcription** (requires Deepgram API key)
- ✅ **SOAP Note Generation** (works completely offline)
- ✅ **Case Storage & Retrieval** (local Qdrant database)
- ✅ **Knowledge Base Search** (local vector database)
- ✅ **Similar Case Recall** (semantic search)
- ✅ **Patient Data Management** (local storage)
- ✅ **Clinical Analytics** (pattern analysis)

### Limited Features (Require Internet):
- ⚠️ **RAG Clinical Suggestions** (requires Gemini API - can use Ollama locally)
- ⚠️ **Knowledge Base Updates** (requires internet for scraping)

---

## 🚀 Quick Setup for Offline Demo

### Step 1: Pre-Configure API Keys (Before Going Offline)

Before deploying to an offline location, configure API keys on a machine with internet:

```bash
# Create .env file
cp .env.example .env

# Add your API keys
DEEPGRAM_API_KEY=your_deepgram_key_here
GOOGLE_API_KEY=your_gemini_key_here  # Optional - for RAG suggestions
```

**Note**: Once configured, these keys work offline (they're just authentication tokens).

---

### Step 2: Install Dependencies (On Machine with Internet)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

### Step 3: Start Qdrant Database (Local - No Internet Needed)

**Windows:**
```powershell
docker run -d `
  -p 6334:6333 `
  -p 6335:6334 `
  --name hygiaai-qdrant `
  -v hygiaai-qdrant-data:/qdrant/storage `
  qdrant/qdrant
```

**Linux/Mac:**
```bash
docker run -d \
  -p 6334:6333 \
  -p 6335:6334 \
  --name hygiaai-qdrant \
  -v hygiaai-qdrant-data:/qdrant/storage \
  qdrant/qdrant
```

**Verify it's running:**
```bash
curl http://localhost:6334/health
# Should return: {"status":"ok"}
```

---

### Step 4: Populate Demo Data (Before Going Offline)

Populate the knowledge base and sample cases:

```bash
# Populate knowledge base with medical information
python scripts/populate_medical_knowledge_base.py

# Populate realistic patient cases
python scripts/populate_extended_demo_data.py

# Optional: Scrape NCBI knowledge (requires internet)
# python scripts/scrape_ncbi_knowledge_base.py
```

---

### Step 5: Start Backend Server

```bash
# Start the FastAPI backend
python run_server.py
```

The server will start on `http://localhost:8000`

---

### Step 6: Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 🎬 Demo Scenarios for Rural/Offline Settings

### Demo 1: Live Transcription & SOAP Note Generation

**Setup:**
1. Open browser to `http://localhost:3000`
2. Navigate to "Live Transcription" page
3. Click "Start Recording"

**Demo Flow:**
1. **Record a consultation** (speak into microphone):
   ```
   "Patient presents with fever, cough, and body aches for 3 days. 
   Temperature is 38.5°C. Blood pressure 120/80. Heart rate 95 bpm. 
   Patient reports difficulty sleeping due to cough. 
   Assessment: Likely viral upper respiratory infection. 
   Plan: Symptomatic treatment with paracetamol, rest, and fluids."
   ```

2. **Show Real-Time Transcription** - Watch as words appear in real-time

3. **Generate SOAP Note** - Click "Generate SOAP Note" button
   - Shows structured SOAP format
   - Extracts Subjective, Objective, Assessment, Plan

4. **Save to Cases** - Click "Save to Cases"
   - Case is stored in local Qdrant database
   - Can be retrieved later

---

### Demo 2: Upload Audio File & Get SOAP Note

**Setup:**
1. Prepare an audio file (WAV, MP3, etc.) with a clinical consultation
2. Navigate to "Live Transcription" page

**Demo Flow:**
1. **Upload Audio File** - Click "Choose File" and select audio file
2. **Automatic Transcription** - File is transcribed automatically
3. **SOAP Note Generated** - SOAP note appears automatically below transcript
4. **Review Sections** - Show S, O, A, P sections

---

### Demo 3: Patient Data Upload with RAG Suggestions

**Setup:**
1. Navigate to "Multimodal Input" page
2. Fill in patient information

**Demo Flow:**
1. **Enter Patient Info:**
   - Patient ID: `DEMO001`
   - Age Group: `Adult`
   - Region: `Rural Kerala`
   - Diagnosis: `Pneumonia`

2. **Upload Transcript or Audio:**
   - Paste transcript text OR
   - Upload audio file

3. **View RAG Suggestions** (if Gemini API configured):
   - Differential diagnoses
   - Treatment recommendations
   - Clinical summary

4. **Show Similar Cases** - System retrieves similar cases from local database

---

### Demo 4: Knowledge Base Search

**Setup:**
1. Navigate to "Knowledge Base" page
2. Ensure knowledge base is populated

**Demo Flow:**
1. **Browse All Entries** - Shows all knowledge base entries
2. **Search for Clinical Information:**
   - Query: "hypertension treatment guidelines"
   - Shows relevant medical literature
   - Displays sources, domains, years

3. **Filter by Domain:**
   - Select "treatment_guidelines"
   - Shows filtered results

4. **Upload Medical Document:**
   - Click "Upload File"
   - Upload a PDF/DOCX medical document
   - Document is processed and added to knowledge base
   - Searchable immediately

---

### Demo 5: Case Recall & Similar Cases

**Setup:**
1. Navigate to "Case Viewer" or use API
2. Ensure sample cases are populated

**Demo Flow:**
1. **Search for Similar Cases:**
   - Enter symptoms: "fever, cough, chest pain"
   - System finds similar cases from local database
   - Shows similarity scores

2. **View Case Details:**
   - Click on a case
   - View full patient timeline
   - See SOAP notes, diagnoses, outcomes

3. **Pattern Analysis:**
   - Show how system identifies patterns
   - Regional health trends
   - Common diagnoses

---

## 🔧 Offline Configuration

### Option 1: Full Offline Mode (No External APIs)

Create `.env` file:

```bash
# Qdrant (Local)
QDRANT_HOST=localhost
QDRANT_PORT=6334

# Disable features requiring internet
ENABLE_RAG=false  # Disable RAG if no LLM available

# Local storage
DATA_DIR=./data
LOGS_DIR=./logs
```

**What Works:**
- ✅ Transcription (if Deepgram key pre-configured)
- ✅ SOAP generation
- ✅ Case storage/retrieval
- ✅ Knowledge base search
- ❌ RAG suggestions (requires LLM)

---

### Option 2: Offline with Local LLM (Ollama)

For full functionality including RAG suggestions:

**1. Install Ollama:**
```bash
# Download from https://ollama.ai
# Install on local machine
```

**2. Pull Medical Model:**
```bash
ollama pull llama3.1:latest
# Or use a medical-specific model if available
```

**3. Update Code to Support Ollama:**

Currently, the system uses Gemini. For offline demo, you can:
- Option A: Use Gemini API key (works offline once configured)
- Option B: Modify code to use Ollama (requires code changes)

**4. Configure `.env`:**
```bash
# Use Ollama instead of Gemini
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_MODEL=llama3.1:latest
```

---

## 📦 Pre-Packaging for Offline Deployment

### Create Deployment Package

**1. Export Docker Images:**
```bash
# Save Qdrant image
docker save qdrant/qdrant:latest -o qdrant-image.tar

# Save any other required images
```

**2. Package Application:**
```bash
# Create deployment package
tar -czf hygiaai-offline-demo.tar.gz \
  . \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='__pycache__'
```

**3. Include Pre-Populated Data:**
```bash
# Export Qdrant data
docker exec hygiaai-qdrant qdrant export --output /qdrant/backup.json

# Copy backup
docker cp hygiaai-qdrant:/qdrant/backup.json ./qdrant-backup.json
```

---

## 🎯 Demo Checklist

### Before Demo:
- [ ] Qdrant database running
- [ ] Backend server started (`python run_server.py`)
- [ ] Frontend running (`npm run dev`)
- [ ] Sample data populated
- [ ] Knowledge base populated
- [ ] API keys configured (Deepgram, Gemini)
- [ ] Test audio file ready
- [ ] Browser opened to `http://localhost:3000`

### During Demo:
- [ ] Show live transcription
- [ ] Upload audio file and show SOAP note
- [ ] Upload patient data and show RAG suggestions
- [ ] Search knowledge base
- [ ] Show similar case recall
- [ ] Demonstrate offline capabilities

---

## 💡 Tips for Rural/Offline Demos

### 1. **Pre-Populate Everything**
- Load knowledge base before demo
- Add sample patient cases
- Test all features beforehand

### 2. **Use Pre-Recorded Audio**
- Have audio files ready
- Test transcription quality
- Ensure SOAP generation works

### 3. **Prepare Demo Script**
- Write down exact steps
- Have backup scenarios ready
- Prepare answers to common questions

### 4. **Show Offline Capabilities**
- Disconnect internet during demo
- Show that core features still work
- Highlight local data storage

### 5. **Performance Optimization**
- Use smaller models if needed
- Optimize Qdrant for local storage
- Pre-load frequently accessed data

---

## 🔍 Troubleshooting Offline Issues

### Issue: "Network error: Unable to connect to server"

**Solution:**
- Ensure backend is running: `python run_server.py`
- Check backend is on `http://localhost:8000`
- Verify frontend `VITE_API_BASE_URL` is correct

### Issue: "Deepgram API key not configured"

**Solution:**
- Add `DEEPGRAM_API_KEY` to `.env` file
- Restart backend server
- Key works offline once configured

### Issue: "No RAG suggestions generated"

**Solution:**
- Check `GOOGLE_API_KEY` is in `.env`
- RAG is optional - core features work without it
- For offline, consider using Ollama (requires code modification)

### Issue: "Qdrant connection failed"

**Solution:**
- Check Docker is running: `docker ps`
- Verify Qdrant container: `docker ps | grep qdrant`
- Check ports: `curl http://localhost:6334/health`

---

## 📱 Mobile/Tablet Demo Setup

For demonstrating on tablets in rural clinics:

### 1. **Build Production Frontend:**
```bash
cd frontend
npm run build
```

### 2. **Serve Static Files:**
```bash
# Option A: Use Python HTTP server
cd frontend/dist
python -m http.server 3000

# Option B: Use backend to serve static files
# (Configure FastAPI to serve frontend build)
```

### 3. **Access from Tablet:**
- Connect tablet to same WiFi network as server
- Access: `http://SERVER_IP:3000`
- Or use: `http://SERVER_IP:8000` (if backend serves frontend)

---

## 🎓 Training Materials for Rural Healthcare Workers

### Quick Reference Card

**Starting the System:**
1. Start Qdrant: `docker start hygiaai-qdrant`
2. Start Backend: `python run_server.py`
3. Open Browser: `http://localhost:3000`

**Recording a Consultation:**
1. Go to "Live Transcription"
2. Click "Start Recording"
3. Speak clearly into microphone
4. Click "Stop" when done
5. Review transcript and SOAP note

**Uploading Patient Data:**
1. Go to "Multimodal Input"
2. Enter patient information
3. Upload audio/text/image
4. Review AI suggestions

**Searching Knowledge Base:**
1. Go to "Knowledge Base"
2. Enter search query
3. Review results
4. Upload new documents if needed

---

## 📊 System Requirements for Offline Demo

### Minimum Requirements:
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 20GB free
- **OS**: Windows 10/11, Linux, or macOS

### Recommended for Smooth Demo:
- **CPU**: 8+ cores
- **RAM**: 16GB
- **Storage**: 50GB+ free
- **GPU**: Optional (for faster embeddings)

---

## 🚀 Quick Start Script

Create `start_offline_demo.ps1` (Windows) or `start_offline_demo.sh` (Linux):

**Windows (`start_offline_demo.ps1`):**
```powershell
# Start Qdrant
Write-Host "Starting Qdrant..."
docker start hygiaai-qdrant
Start-Sleep -Seconds 5

# Start Backend
Write-Host "Starting Backend..."
Start-Process python -ArgumentList "run_server.py" -WindowStyle Minimized

# Start Frontend
Write-Host "Starting Frontend..."
Set-Location frontend
Start-Process npm -ArgumentList "run", "dev"

Write-Host "✅ Demo ready! Open http://localhost:3000"
```

**Linux/Mac (`start_offline_demo.sh`):**
```bash
#!/bin/bash
echo "Starting Qdrant..."
docker start hygiaai-qdrant
sleep 5

echo "Starting Backend..."
python run_server.py &
sleep 3

echo "Starting Frontend..."
cd frontend
npm run dev &

echo "✅ Demo ready! Open http://localhost:3000"
```

---

## 📝 Summary

**For Offline/Rural Demo:**
1. ✅ Pre-configure API keys (works offline once set)
2. ✅ Start Qdrant database locally
3. ✅ Populate demo data
4. ✅ Start backend and frontend
5. ✅ Demonstrate features:
   - Live transcription
   - Audio file upload → SOAP note
   - Patient data upload → RAG suggestions
   - Knowledge base search
   - Similar case recall

**Key Points:**
- Core features work completely offline
- API keys work offline (just authentication tokens)
- All data stored locally in Qdrant
- No internet required for demo
- RAG suggestions optional (can use Ollama for fully offline)

---

## 🆘 Need Help?

If you encounter issues during offline demo:
1. Check backend logs: `logs/hygiaai.log`
2. Verify Qdrant: `curl http://localhost:6334/health`
3. Check browser console for frontend errors
4. Ensure all services are running

For questions or support, refer to:
- `TROUBLESHOOTING_NETWORK_ERRORS.md`
- `QUICK_START.md`
- `START_SERVER.md`

