# How to Start the Backend Server

## ⚠️ Current Issue

The backend server appears to be running but may be in a bad state (many CLOSE_WAIT connections). 

## 🔄 Solution: Restart the Server

### Step 1: Stop the Current Server

**Option A: Find and Kill the Process**
```powershell
# Find the process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with the actual process ID)
taskkill /PID <PID> /F
```

**Option B: Press Ctrl+C in the terminal where the server is running**

### Step 2: Start the Server Fresh

Open a **new terminal/PowerShell** window and run:

```powershell
# Navigate to project directory
cd C:\Users\LEGION\Desktop\Projects\HygiaAI----Real-Time-Clinical-Voice-Assistant

# Activate virtual environment (if using one)
.venv\Scripts\Activate.ps1

# Start the server
python run_server.py
```

### Step 3: Verify Server is Running

Open a browser and visit: **http://localhost:8000/health**

You should see:
```json
{"status":"healthy"}
```

### Step 4: Refresh Your Frontend

Once the server is running properly:
1. Refresh your browser (F5)
2. The Knowledge Browser should load
3. File uploads should work

---

## 🐛 If Server Still Won't Start

1. **Check for Python errors:**
   - Look at the terminal output
   - Common issues: missing dependencies, import errors

2. **Install/Update dependencies:**
   ```powershell
   pip install -r requirements.txt --upgrade
   ```

3. **Check environment variables:**
   - Make sure `.env` file exists
   - Verify API keys are set (at minimum, DEEPGRAM_API_KEY for transcription)

4. **Check Qdrant connection:**
   - If using local Qdrant: `docker ps` to see if Qdrant container is running
   - If using cloud: Verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`

---

## 📋 Quick Checklist

- [ ] Server process killed/stopped
- [ ] New terminal opened
- [ ] Virtual environment activated (if using one)
- [ ] `python run_server.py` executed
- [ ] Server shows "Application startup complete"
- [ ] `http://localhost:8000/health` returns `{"status":"healthy"}`
- [ ] Frontend refreshed

---

**The server must be running for the frontend to work!**

