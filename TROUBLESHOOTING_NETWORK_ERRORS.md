# Troubleshooting Network Errors

## 🔍 Current Issue

You're seeing: `Network error: Unable to connect to server`

## ✅ Server Status Check

The backend server **IS running** and responding:
- Health endpoint: `http://localhost:8000/health` ✅ Returns `{"status":"healthy"}`
- Server is listening on port 8000 ✅

## 🔧 Possible Causes & Solutions

### 1. **Frontend Not Connecting to Backend**

**Check:**
- Open browser DevTools (F12)
- Go to Network tab
- Try to use the Knowledge Browser or upload a file
- Look for failed requests to `http://localhost:8000`

**Solution:**
- Make sure frontend is running: `cd frontend && npm run dev`
- Check frontend URL (usually `http://localhost:3000` or `http://localhost:5173`)
- Verify `API_BASE_URL` in browser console:
  ```javascript
  // In browser console:
  console.log(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
  ```

### 2. **CORS Issues**

**Check:**
- Look for CORS errors in browser console
- Error message: "Access to XMLHttpRequest blocked by CORS policy"

**Solution:**
- Backend already allows all origins (`allow_origins=["*"]`)
- If still having issues, restart the backend server

### 3. **Backend Server Hung/Stuck**

**Symptoms:**
- Many CLOSE_WAIT connections
- Server responds to health check but not to API requests

**Solution:**
1. Stop the server (Ctrl+C or kill process)
2. Restart: `python run_server.py`
3. Wait for "Application startup complete" message

### 4. **Port Conflict**

**Check:**
```powershell
netstat -ano | findstr :8000
```

**Solution:**
- Kill any processes using port 8000
- Restart server

### 5. **Firewall/Antivirus Blocking**

**Check:**
- Windows Firewall might be blocking connections
- Antivirus might be interfering

**Solution:**
- Temporarily disable firewall/antivirus to test
- Add exception for Python/uvicorn

---

## 🧪 Quick Test

Run these commands to verify everything:

```powershell
# 1. Test backend health
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing

# 2. Test knowledge domains endpoint
Invoke-WebRequest -Uri http://localhost:8000/api/v1/clinical_memory/knowledge/domains -UseBasicParsing

# 3. Check if frontend can reach backend
# Open browser console and run:
fetch('http://localhost:8000/health').then(r => r.json()).then(console.log)
```

---

## 📝 Step-by-Step Fix

1. **Stop Backend:**
   ```powershell
   # Find process
   netstat -ano | findstr :8000
   # Kill it (replace <PID>)
   taskkill /PID <PID> /F
   ```

2. **Restart Backend:**
   ```powershell
   python run_server.py
   ```

3. **Verify Backend:**
   - Visit: `http://localhost:8000/health`
   - Should see: `{"status":"healthy"}`

4. **Restart Frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```

5. **Test in Browser:**
   - Open frontend URL
   - Open DevTools (F12) → Network tab
   - Try using Knowledge Browser
   - Check for failed requests

---

## 🆘 Still Not Working?

1. **Check browser console** for detailed error messages
2. **Check backend terminal** for error logs
3. **Verify `.env` file** exists with required API keys
4. **Check Qdrant connection** (if using cloud Qdrant)

---

**Most Common Fix:** Simply restart both the backend and frontend servers!

