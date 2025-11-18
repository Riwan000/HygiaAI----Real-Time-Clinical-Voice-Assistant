# Railway Network & Configuration Settings

## ✅ What Railway Sets Automatically (DO NOT CHANGE)

1. **PORT** - Railway automatically injects this variable
   - ❌ **DO NOT** manually set `PORT` in Railway variables
   - ✅ Your app reads it via `os.getenv("PORT", "8000")`
   - Railway uses this for healthchecks automatically

2. **Healthcheck Hostname** - Railway uses `healthcheck.railway.app`
   - ✅ Already handled by binding to `0.0.0.0`
   - ✅ CORS middleware allows all origins

---

## 🔧 What You NEED to Configure in Railway Dashboard

### 1. **Service Settings → Networking**

- ✅ **Public Networking:** Enable this
- ✅ **Generate Domain:** Click to get your public URL
- Your backend will be at: `https://your-service.railway.app`

### 2. **Service Settings → Healthcheck**

- ✅ **Healthcheck Path:** `/health` (already set in `railway.json`)
- ⚠️ **Healthcheck Timeout:** Default is 300 seconds (5 minutes)
  - If your app takes longer to start, increase this:
  - Go to **Variables** tab → Add: `RAILWAY_HEALTHCHECK_TIMEOUT_SEC=600`
  - Or set in Railway dashboard → Settings → Healthcheck Timeout

### 3. **Service Settings → Variables** (CRITICAL)

Add these environment variables in Railway dashboard:

#### Required for Basic Operation:
```bash
# Qdrant Configuration (if using Qdrant Cloud)
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here

# OR if using Railway-hosted Qdrant
QDRANT_HOST=your-qdrant-service.railway.app
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key_if_set
```

#### Optional but Recommended:
```bash
# API Keys for features
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_GENERATIVE_AI_KEY=your_gemini_key

# CORS (after frontend is deployed)
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# Increase healthcheck timeout if needed (in seconds)
RAILWAY_HEALTHCHECK_TIMEOUT_SEC=600
```

#### ⚠️ DO NOT SET:
```bash
# ❌ PORT=8000  # Railway sets this automatically!
# ❌ HOST=0.0.0.0  # Not needed, handled in code
```

---

## 🌐 Network Configuration Checklist

### In Railway Dashboard → Your Service → Settings:

- [ ] **Public Networking:** ✅ Enabled
- [ ] **Domain Generated:** ✅ Yes (copy the domain)
- [ ] **Healthcheck Path:** `/health` ✅
- [ ] **Healthcheck Timeout:** 300 seconds (or increase if needed)
- [ ] **Restart Policy:** On Failure ✅
- [ ] **Max Restart Retries:** 10 ✅

### In Railway Dashboard → Your Service → Variables:

- [ ] `QDRANT_HOST` - Set to your Qdrant instance
- [ ] `QDRANT_PORT` - Set to `6333` (or your Qdrant port)
- [ ] `QDRANT_API_KEY` - Set if using Qdrant Cloud or secured instance
- [ ] `DEEPGRAM_API_KEY` - Optional, for transcription
- [ ] `GOOGLE_GENERATIVE_AI_KEY` - Optional, for LLM features
- [ ] `ALLOWED_ORIGINS` - Set after frontend is deployed

---

## 🔍 How to Verify Network Settings

### 1. Check Healthcheck is Working:
```bash
# Railway will automatically check:
curl https://your-service.railway.app/health
# Should return: {"status": "ok"}
```

### 2. Check Server is Listening:
In Railway logs, you should see:
```
Starting uvicorn server on port {PORT}...
Server will listen on 0.0.0.0:{PORT}
Uvicorn running on 0.0.0.0:{PORT}
```

### 3. Check Port Binding:
Railway automatically assigns a port. Your app reads it via:
```python
port = os.getenv("PORT", "8000")  # Railway injects PORT
```

---

## 🚨 Common Network Issues

### Issue: Healthcheck fails with "service unavailable"

**Check:**
1. ✅ Is `PORT` variable being read correctly? (Check logs)
2. ✅ Is server binding to `0.0.0.0`? (Check logs)
3. ✅ Is `/health` endpoint returning 200? (Test manually)
4. ✅ Is healthcheck timeout long enough? (Increase if needed)

### Issue: Can't connect to Qdrant

**Check:**
1. ✅ Is `QDRANT_HOST` set correctly?
2. ✅ Is Qdrant service public networking enabled?
3. ✅ Is `QDRANT_PORT` correct? (6333 for HTTP, 6334 for gRPC)
4. ✅ Is `QDRANT_API_KEY` set if required?

### Issue: CORS errors from frontend

**Check:**
1. ✅ Is `ALLOWED_ORIGINS` set in Railway variables?
2. ✅ Does it include your frontend domain?
3. ✅ Format: `https://domain1.com,https://domain2.com` (comma-separated)

---

## 📝 Quick Setup Summary

1. **Enable Public Networking** ✅
2. **Set Healthcheck Path:** `/health` ✅ (already in railway.json)
3. **Add Environment Variables:**
   - `QDRANT_HOST`
   - `QDRANT_PORT=6333`
   - `QDRANT_API_KEY` (if needed)
4. **DO NOT set PORT** - Railway handles this automatically
5. **Test:** Wait for deployment, check logs for "Uvicorn running"

---

## 🎯 Minimal Configuration (Just to Get Started)

If you just want to test the healthcheck:

1. **Enable Public Networking** ✅
2. **Healthcheck Path:** `/health` ✅ (already configured)
3. **No variables needed** for basic healthcheck to pass

The health endpoint doesn't require any external services, so it should work immediately!

