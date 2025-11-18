# Quick Start Guide

## 🚀 Starting the Backend Server

The backend server must be running for the frontend to work. Follow these steps:

### 1. **Start the Backend Server**

Open a terminal/PowerShell in the project root and run:

```bash
python run_server.py
```

Or directly with uvicorn:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. **Verify Server is Running**

Open your browser and visit: `http://localhost:8000/health`

You should see:
```json
{"status":"healthy"}
```

### 3. **Start the Frontend** (in a separate terminal)

```bash
cd frontend
npm run dev
```

The frontend will typically run on `http://localhost:3000` or `http://localhost:5173`

---

## 🔧 Troubleshooting

### Server Won't Start

1. **Check if port 8000 is already in use:**
   ```powershell
   netstat -ano | findstr :8000
   ```

2. **Kill the process if needed:**
   ```powershell
   taskkill /PID <process_id> /F
   ```

3. **Check for Python errors:**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check `.env` file has required API keys

### Network Errors in Frontend

1. **Verify backend is running:**
   - Visit `http://localhost:8000/health` in browser
   - Should return `{"status":"healthy"}`

2. **Check CORS settings:**
   - Backend should allow `http://localhost:3000` or your frontend URL
   - Check `src/api/main.py` for CORS configuration

3. **Check API base URL:**
   - Frontend uses `http://localhost:8000` by default
   - Can be overridden with `VITE_API_BASE_URL` environment variable

---

## 📝 Required Environment Variables

Create a `.env` file in the project root:

```bash
# Deepgram (for transcription)
DEEPGRAM_API_KEY=your_key_here

# Google Gemini (for RAG insights)
GOOGLE_API_KEY=your_key_here

# Qdrant (for cloud deployment)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_key_here

# Or for local Qdrant:
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## ✅ Quick Test

Once both servers are running:

1. **Backend Health:** `http://localhost:8000/health`
2. **Frontend:** Open `http://localhost:3000` (or your frontend URL)
3. **Test Knowledge Base:** Navigate to Knowledge page
4. **Test Transcription:** Navigate to Transcription page

---

**Note:** Both servers must be running simultaneously for the application to work!

