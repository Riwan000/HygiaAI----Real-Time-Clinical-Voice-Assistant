# HygiaAI Deployment Steps

Complete step-by-step guide to deploy HygiaAI for demo or production.

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ Python 3.8+ installed
- ✅ Node.js 20.19+ or 22.12+ installed
- ✅ Docker Desktop installed and running (for Qdrant)
- ✅ API Keys configured:
  - Deepgram API key (for transcription)
  - LLM API key (OpenAI, Anthropic, or OpenRouter - optional for demo)

---

## 🚀 Deployment Steps

### Step 1: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Deepgram API (Required for transcription)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# LLM API Keys (Choose one or more - Optional for demo)
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Qdrant Configuration (Optional - defaults shown)
QDRANT_HOST=localhost
QDRANT_PORT=6334

# Ollama (Optional - for local fallback)
OLLAMA_BASE_URL=http://localhost:11434/v1
```

**Note**: For demo purposes, you only need `DEEPGRAM_API_KEY`. LLM keys are optional.

---

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected output**: All packages installed successfully.

---

### Step 3: Start Qdrant Vector Database

**Option A: Using Docker (Recommended)**

**Windows (PowerShell):**
```powershell
.\examples\setup_qdrant.ps1
```

**Linux/Mac:**
```bash
chmod +x examples/setup_qdrant.sh
./examples/setup_qdrant.sh
```

**Option B: Manual Docker Command**
```bash
docker run -d -p 6334:6333 -p 6335:6334 --name hygiaai-qdrant -v hygiaai-qdrant-data:/qdrant/storage qdrant/qdrant
```

**Verify Qdrant is running:**
```bash
# Check health
curl http://localhost:6334/health

# Or open in browser
# http://localhost:6334/dashboard
```

**Expected output**: `{"status":"ok"}` or dashboard loads successfully.

---

### Step 4: Populate Sample Data

**4a. Populate Clinical Cases:**
```bash
python scripts/populate_realistic_cases.py
```

**Expected output**: 
```
✅ Cases processed: 10
✅ Cases stored: 10
```

**4b. Populate Knowledge Base:**
```bash
python scripts/populate_knowledge_base_complete.py
```

**Expected output**:
```
✅ Documents processed: 6 (curated)
✅ Documents ingested: 9 (internet-sourced)
```

**Verify data:**
- Open Qdrant dashboard: http://localhost:6334/dashboard
- Check collections: `hygiaai_clinical_cases` and `hygiaai_knowledge_base`

---

### Step 5: Start Backend Server

**Terminal 1 - Backend:**
```bash
python run_server.py
```

**Expected output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify backend:**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

**Expected response**: `{"status":"healthy","service":"HygiaAI API"}`

---

### Step 6: Start Frontend

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Expected output**:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**Verify frontend:**
- Open browser: http://localhost:3000
- Should see the HygiaAI interface

---

### Step 7: Verify Deployment

**Check all services:**

1. **Qdrant**: http://localhost:6334/health
   - Should return: `{"status":"ok"}`

2. **Backend API**: http://localhost:8000/health
   - Should return: `{"status":"healthy","service":"HygiaAI API"}`

3. **Frontend**: http://localhost:3000
   - Should load the application interface

4. **API Documentation**: http://localhost:8000/docs
   - Should show Swagger UI with all endpoints

---

## 🎯 Quick Verification Checklist

- [ ] Qdrant running on port 6334
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] 10 clinical cases populated
- [ ] 15 knowledge base documents populated
- [ ] Deepgram API key configured
- [ ] All services responding to health checks

---

## 🧪 Test the Deployment

### Test 1: Case Search
1. Navigate to Dashboard/Case Search
2. Enter search query: "cough with fever"
3. Should see similar cases with similarity scores

### Test 2: SOAP Notes
1. Navigate to SOAP Notes page
2. Click on a SOAP note
3. Verify sections expand/collapse
4. Test PDF export

### Test 3: Analytics
1. Navigate to Analytics page
2. Verify charts load
3. Test filters (time range, region, disease type)
4. Verify outbreak alerts appear (if applicable)

### Test 4: Knowledge Base
1. Navigate to Knowledge Base page
2. Search for: "vital signs normal values"
3. Verify results appear with domain categorization

### Test 5: Live Transcription (Optional)
1. Navigate to Live Transcription page
2. Click "Start Recording"
3. Speak a test consultation
4. Verify real-time transcription appears
5. Test SOAP note generation

---

## 🐛 Troubleshooting

### Qdrant Not Starting

**Issue**: Docker container fails to start
```bash
# Check if port is in use
netstat -an | findstr 6334

# Remove existing container
docker rm -f hygiaai-qdrant

# Start fresh
docker run -d -p 6334:6333 -p 6335:6334 --name hygiaai-qdrant qdrant/qdrant
```

### Backend Not Starting

**Issue**: Port 8000 already in use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process or change port in run_server.py
```

**Issue**: Missing dependencies
```bash
pip install -r requirements.txt
```

### Frontend Not Starting

**Issue**: Port 3000 already in use
```bash
# Vite will automatically use next available port
# Or specify: npm run dev -- --port 3001
```

**Issue**: Node modules not installed
```bash
cd frontend
rm -rf node_modules
npm install
```

### Data Not Showing

**Issue**: Cases not populated
```bash
# Re-populate cases
python scripts/populate_realistic_cases.py

# Verify in Qdrant dashboard
# http://localhost:6334/dashboard
```

**Issue**: Knowledge base empty
```bash
# Re-populate knowledge base
python scripts/populate_knowledge_base_complete.py
```

### Transcription Not Working

**Issue**: Deepgram API key not configured
```bash
# Check .env file exists and has DEEPGRAM_API_KEY
# Verify key is valid at https://console.deepgram.com
```

---

## 📊 Service URLs Summary

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main application interface |
| Backend API | http://localhost:8000 | REST API endpoints |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Qdrant Dashboard | http://localhost:6334/dashboard | Vector database UI |
| Qdrant API | http://localhost:6334 | Qdrant REST API |

---

## 🎬 Demo Quick Start (All-in-One)

For a quick demo setup, run these commands in order:

```bash
# 1. Start Qdrant
docker run -d -p 6334:6333 -p 6335:6334 --name hygiaai-qdrant qdrant/qdrant

# 2. Populate data (wait for Qdrant to be ready - ~10 seconds)
python scripts/populate_realistic_cases.py
python scripts/populate_knowledge_base_complete.py

# 3. Start backend (in separate terminal)
python run_server.py

# 4. Start frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

**Total setup time**: ~5-10 minutes

---

## 🔄 Stopping Services

**Stop Frontend:**
- Press `Ctrl+C` in frontend terminal

**Stop Backend:**
- Press `Ctrl+C` in backend terminal

**Stop Qdrant:**
```bash
docker stop hygiaai-qdrant
```

**Remove Qdrant (if needed):**
```bash
docker stop hygiaai-qdrant
docker rm hygiaai-qdrant
```

---

## 📝 Production Deployment

For production deployment, use the offline deployment kit:

```bash
# See deployment/offline/INSTALLATION_GUIDE.md
cd deployment/offline
.\install.ps1  # Windows
# OR
./install.sh  # Linux
```

---

## ✅ Deployment Complete!

Once all steps are complete, you should have:

- ✅ Qdrant running with sample data
- ✅ Backend API accessible
- ✅ Frontend application running
- ✅ All features ready for demo

**Next**: Start demonstrating the features! 🎉

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0.0

