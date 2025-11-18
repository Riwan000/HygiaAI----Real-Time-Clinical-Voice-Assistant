# Railway Deployment Configuration Guide

## Quick Setup for Railway

Based on your Railway dashboard, here are the exact settings to use:

---

## 📋 Railway Configuration Settings

### 1. **Root Directory**
Leave empty (project root) OR set to: `.`

Railway will detect Python automatically.

---

### 2. **Build Command**
```
pip install -r requirements.txt
```

**OR** leave empty - Railway will auto-detect and run this.

---

### 3. **Start Command** ⚠️ IMPORTANT
```
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

**Note:** Railway provides `$PORT` environment variable automatically. Use this instead of hardcoded port 8000.

---

### 4. **Healthcheck Path**
```
/health
```

This will check `https://your-app.railway.app/health` to verify deployment is live.

---

### 5. **Environment Variables** (Add these in Railway dashboard)

Click **"Variables"** tab and add:

#### Required:
```
DEEPGRAM_API_KEY=your_deepgram_api_key_here
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key
PORT=8000
```

#### Optional (for LLM features):
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key
```

#### For CORS (after frontend is deployed):
```
ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:3000
```

---

### 6. **Resource Limits** (Free Tier)
- **CPU:** 2 vCPU (max)
- **Memory:** 1 GB (max)

These are fine for demos. Upgrade if you need more.

---

### 7. **Restart Policy**
- **On Failure:** ✅ Enabled
- **Max restart retries:** 10

This ensures your service restarts if it crashes.

---

### 8. **Networking**
- **Public Networking:** ✅ Enabled
- **Generate Domain:** Click this to get your backend URL

Your backend will be accessible at: `https://your-app.railway.app`

---

## 🚀 Deployment Steps

1. **Configure Settings:**
   - Set Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - Set Healthcheck Path: `/health`

2. **Add Environment Variables:**
   - Go to "Variables" tab
   - Add all required env vars listed above

3. **Generate Domain:**
   - Click "Generate Domain" in Networking section
   - Copy the URL (e.g., `https://hygiaai-backend.railway.app`)

4. **Deploy:**
   - Railway will auto-deploy when you push to GitHub
   - Or click "Deploy" manually

5. **Verify:**
   - Check deployment logs
   - Visit: `https://your-app.railway.app/health`
   - Should return: `{"status":"healthy","service":"HygiaAI API"}`

---

## 🔧 Troubleshooting

### Build Fails

**Issue:** `pip install` fails

**Solution:**
- Check `requirements.txt` exists in root
- Verify Python version (Railway uses Python 3.11+)
- Check build logs for specific error

---

### Service Won't Start

**Issue:** Application crashes on startup

**Solution:**
1. Check Start Command is correct:
   ```
   uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

2. Verify environment variables are set:
   - `DEEPGRAM_API_KEY` is required
   - `QDRANT_HOST` and `QDRANT_API_KEY` are required

3. Check logs in Railway dashboard for errors

---

### Healthcheck Fails

**Issue:** Deployment shows as unhealthy

**Solution:**
1. Verify `/health` endpoint exists (it does in `src/api/main.py`)
2. Check healthcheck path is set to: `/health`
3. Wait a few minutes - first deployment can take time

---

### Port Issues

**Issue:** Service can't bind to port

**Solution:**
- **Always use `$PORT`** in start command, not hardcoded `8000`
- Railway assigns a random port via `$PORT` environment variable

---

## 📝 Example Railway Config File

If you want to use `railway.json` (Config-as-code):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health"
  }
}
```

Add this file path in Railway: `railway.json`

---

## ✅ Checklist

Before deploying, ensure:

- [ ] Start Command uses `$PORT` not `8000`
- [ ] Healthcheck Path set to `/health`
- [ ] All environment variables added
- [ ] `requirements.txt` exists in root directory
- [ ] Public Networking enabled
- [ ] Domain generated

---

## 🎯 Next Steps After Deployment

1. **Get your backend URL:**
   - Copy from Railway dashboard (e.g., `https://hygiaai-backend.railway.app`)

2. **Update Frontend:**
   - In Vercel, add env var: `VITE_API_BASE_URL=https://your-backend.railway.app`

3. **Update CORS:**
   - In Railway, add env var: `ALLOWED_ORIGINS=https://your-frontend.vercel.app`

4. **Test:**
   - Visit: `https://your-backend.railway.app/docs` (API documentation)
   - Visit: `https://your-backend.railway.app/health` (health check)

---

## 💡 Pro Tips

- **Monitor Logs:** Railway dashboard shows real-time logs
- **Auto-Deploy:** Every push to `main` branch auto-deploys
- **Rollback:** Click previous deployment → "Promote" to rollback
- **Metrics:** Railway shows CPU/Memory usage in dashboard

---

**Need Help?** Check Railway logs or see `DEPLOYMENT_CLOUD.md` for full guide.

