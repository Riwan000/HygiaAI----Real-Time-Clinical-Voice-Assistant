# Render Deployment Guide - Step by Step

Complete guide to deploy HygiaAI backend to Render.

---

## 🚀 Quick Deployment (5 Minutes)

### Step 1: Prepare Your Repository

Make sure your code is pushed to GitHub:
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

---

### Step 2: Create Render Account

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Sign up with GitHub (recommended) or email
3. Verify your email if needed

---

### Step 3: Create Web Service

1. **Click "New" → "Web Service"**
2. **Connect GitHub Repository:**
   - Click "Connect account" if not connected
   - Select your repository: `HygiaAI----Real-Time-Clinical-Voice-Assistant`
   - Click "Connect"

---

### Step 4: Configure Service

**Option A: Using render.yaml (Recommended - Automatic)**

1. Render will auto-detect `render.yaml`
2. Review the configuration:
   - **Name:** `hygiaai-backend` (or your choice)
   - **Environment:** Docker (from render.yaml)
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** `.` (project root)

3. **Click "Apply"** to use render.yaml settings

**Option B: Manual Configuration**

If you prefer manual setup:

1. **Basic Settings:**
   ```
   Name: hygiaai-backend
   Environment: Docker
   Region: Choose closest (e.g., Oregon, Frankfurt)
   Branch: main
   Root Directory: . (leave empty)
   ```

2. **Build & Deploy:**
   ```
   Dockerfile Path: ./Dockerfile
   Docker Command: python start_server.py
   ```

3. **Health Check:**
   ```
   Health Check Path: /health
   ```

---

### Step 5: Add Environment Variables

Click "Environment" tab and add:

**Required:**
```bash
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here
```

**Optional (for features):**
```bash
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_GENERATIVE_AI_KEY=your_gemini_key
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

**⚠️ Important:** 
- Do NOT set `PORT` manually - Render sets this automatically
- Use the "Secret" toggle for sensitive keys (recommended)

---

### Step 6: Select Plan

- **Free:** 750 hours/month (sleeps after 15 min inactivity)
  - Good for: Testing, demos
  - ⚠️ First request after sleep takes ~30 seconds
  
- **Starter ($7/month):** Always on, 512 MB RAM
  - Good for: Production, always-available API

**Recommendation:** Start with Free, upgrade if needed.

---

### Step 7: Deploy

1. **Click "Create Web Service"**
2. **Wait for build** (5-10 minutes first time)
3. **Monitor logs** to see progress

---

## ✅ Verification

### Check Deployment Status

1. **In Render Dashboard:**
   - Status should show "Live" (green)
   - Health check should pass

2. **Check Logs:**
   - Click "Logs" tab
   - You should see:
     ```
     === Starting HygiaAI API Server ===
     Starting uvicorn server on port 10000...
     Application startup complete.
     Uvicorn running on 0.0.0.0:10000
     ```

3. **Test Health Endpoint:**
   ```bash
   curl https://hygiaai-backend.onrender.com/health
   ```
   Should return: `{"status":"ok"}`

---

## 🔧 Configuration Details

### render.yaml (Already Configured)

The `render.yaml` file is already set up with:
- ✅ Docker deployment
- ✅ Health check path: `/health`
- ✅ Startup command: `python start_server.py`
- ✅ Environment variable placeholders

### What Render Does Automatically

- ✅ Sets `PORT` environment variable (usually 10000)
- ✅ Provides HTTPS automatically
- ✅ Handles healthchecks
- ✅ Auto-deploys on git push (if enabled)

---

## 🌐 Getting Your Backend URL

After deployment, Render provides:
- **URL:** `https://hygiaai-backend.onrender.com`
- **Custom Domain:** Available in Settings → Custom Domains

**Update Frontend:**
Set `VITE_API_BASE_URL` in your frontend deployment to:
```
https://hygiaai-backend.onrender.com
```

---

## 🔄 Auto-Deploy Setup

1. **In Render Dashboard → Settings:**
   - ✅ **Auto-Deploy:** Enabled by default
   - ✅ **Pull Request Previews:** Enable if you want

2. **Every push to `main` branch:**
   - Render automatically rebuilds and redeploys
   - You'll see deployment status in dashboard

---

## 🐛 Troubleshooting

### Issue: Build Fails

**Check:**
1. ✅ Is `Dockerfile` in project root?
2. ✅ Are all dependencies in `requirements.txt`?
3. ✅ Check build logs for specific errors

**Common Fix:**
- Render might timeout on first build (PyTorch is large)
- Wait for build to complete (can take 10-15 minutes)
- If it fails, try upgrading to Starter plan for faster builds

### Issue: Health Check Fails

**Check:**
1. ✅ Is `/health` endpoint returning 200?
2. ✅ Check logs for server startup messages
3. ✅ Verify `PORT` is being read correctly

**Fix:**
- Check logs for "Starting uvicorn server on port..."
- Verify health endpoint: `curl https://your-app.onrender.com/health`

### Issue: Service Sleeps (Free Tier)

**Symptom:** First request takes 30+ seconds

**Solution:**
- This is normal for free tier
- Upgrade to Starter ($7/month) for always-on
- Or use a ping service to keep it awake (not recommended)

### Issue: Out of Memory

**Symptom:** Service crashes, logs show OOM errors

**Solution:**
- Upgrade to plan with more RAM
- Or optimize Dockerfile to reduce memory usage

---

## 📊 Render vs Railway Comparison

| Feature | Render | Railway |
|---------|--------|---------|
| **Free Tier** | ✅ 750 hrs/month | ✅ $5 credit |
| **Always-On** | ❌ Sleeps (free) | ✅ Always on |
| **Docker Support** | ✅ Yes | ✅ Yes |
| **Auto-Deploy** | ✅ Yes | ✅ Yes |
| **Health Checks** | ✅ Yes | ✅ Yes |
| **Custom Domains** | ✅ Yes | ✅ Yes |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 Next Steps After Deployment

1. **Test Your Backend:**
   ```bash
   curl https://hygiaai-backend.onrender.com/health
   curl https://hygiaai-backend.onrender.com/
   ```

2. **Update Frontend:**
   - Set `VITE_API_BASE_URL` to your Render URL
   - Redeploy frontend

3. **Monitor:**
   - Check Render dashboard for logs
   - Monitor health status
   - Set up alerts if needed

---

## 💡 Pro Tips

1. **Use render.yaml:** Makes configuration version-controlled
2. **Set secrets properly:** Use "Secret" toggle for API keys
3. **Monitor logs:** First deployment can take 10-15 minutes
4. **Free tier limitation:** Service sleeps after 15 min inactivity
5. **Upgrade when needed:** Starter plan ($7/month) for production

---

**Your backend will be live at:** `https://hygiaai-backend.onrender.com` (or your custom name)

**Ready to deploy?** Follow the steps above and you'll be live in ~10 minutes! 🚀

