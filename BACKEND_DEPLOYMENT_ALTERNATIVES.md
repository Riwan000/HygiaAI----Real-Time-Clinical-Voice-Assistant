# Backend Deployment Alternatives - Quick Guide

Since Railway is having issues, here are the **easiest alternatives** to deploy your FastAPI backend.

---

## 🚀 Option 1: Render (Easiest Alternative - Recommended)

**Best for:** Simple deployment, similar to Railway, free tier available

### Quick Setup (5 minutes):

1. **Go to [Render Dashboard](https://dashboard.render.com)**
2. **Click "New" → "Web Service"**
3. **Connect GitHub Repository:**
   - Select your repository
   - Click "Connect"

4. **Configure Settings:**
   ```
   Name: hygiaai-backend
   Environment: Python 3
   Region: Choose closest to you
   Branch: main
   Root Directory: . (leave empty)
   Build Command: pip install -r requirements.txt
   Start Command: python start_server.py
   ```

5. **Add Environment Variables:**
   ```
   QDRANT_HOST=your-cluster.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_key
   DEEPGRAM_API_KEY=your_key (optional)
   GOOGLE_GENERATIVE_AI_KEY=your_key (optional)
   ```

6. **Select Plan:**
   - **Free:** 750 hours/month (sleeps after 15 min inactivity)
   - **Starter:** $7/month (always on)

7. **Click "Create Web Service"**

**✅ Done!** Your backend will be at: `https://hygiaai-backend.onrender.com`

### Render Advantages:
- ✅ Very similar to Railway
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Healthchecks supported
- ✅ Environment variables easy to set
- ✅ Auto-deploy from GitHub

---

## 🚀 Option 2: Fly.io (Best for Global Distribution)

**Best for:** Global edge deployment, low latency, generous free tier

### Quick Setup:

1. **Install Fly CLI:**
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Initialize (in project root):**
   ```bash
   fly launch
   ```
   - App name: `hygiaai-backend` (or choose your own)
   - Region: Choose closest
   - PostgreSQL: No (we use Qdrant)
   - Redis: No

4. **Edit `fly.toml` (created automatically):**
   ```toml
   app = "hygiaai-backend"
   primary_region = "iad"  # Change to your region
   
   [build]
     dockerfile = "Dockerfile"
   
   [env]
     PORT = "8000"
   
   [[services]]
     internal_port = 8000
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   
     [services.concurrency]
       type = "connections"
       hard_limit = 25
       soft_limit = 20
   
     [[services.http_checks]]
       interval = "10s"
       timeout = "2s"
       grace_period = "5s"
       method = "GET"
       path = "/health"
   ```

5. **Set Secrets (Environment Variables):**
   ```bash
   fly secrets set QDRANT_HOST=your-cluster.qdrant.io
   fly secrets set QDRANT_PORT=6333
   fly secrets set QDRANT_API_KEY=your_key
   fly secrets set DEEPGRAM_API_KEY=your_key
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

**✅ Done!** Your backend will be at: `https://hygiaai-backend.fly.dev`

### Fly.io Advantages:
- ✅ 3 VMs free (generous free tier)
- ✅ Global edge network
- ✅ Very fast
- ✅ Docker-based (uses your existing Dockerfile)
- ✅ Auto-scaling

---

## 🚀 Option 3: Google Cloud Run (Serverless Containers)

**Best for:** Pay-per-use, auto-scaling, serverless

### Quick Setup:

1. **Install Google Cloud SDK:**
   ```bash
   # Windows
   winget install Google.CloudSDK
   
   # Mac
   brew install google-cloud-sdk
   ```

2. **Login and Set Project:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build and Deploy:**
   ```bash
   # Build Docker image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/hygiaai-backend
   
   # Deploy to Cloud Run
   gcloud run deploy hygiaai-backend \
     --image gcr.io/YOUR_PROJECT_ID/hygiaai-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000 \
     --set-env-vars QDRANT_HOST=your-cluster.qdrant.io,QDRANT_PORT=6333
   ```

4. **Set Secrets:**
   ```bash
   # Create secret
   echo -n "your-api-key" | gcloud secrets create qdrant-api-key --data-file=-
   
   # Grant access
   gcloud run services update hygiaai-backend \
     --update-secrets QDRANT_API_KEY=qdrant-api-key:latest
   ```

**✅ Done!** Your backend will be at: `https://hygiaai-backend-xxx-uc.a.run.app`

### Cloud Run Advantages:
- ✅ Pay only for requests (free tier: 2M requests/month)
- ✅ Auto-scales to zero
- ✅ No cold start issues for healthchecks
- ✅ Uses your existing Dockerfile

---

## 🚀 Option 4: DigitalOcean App Platform

**Best for:** Simple pricing, Docker support, always-on

### Quick Setup:

1. **Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)**
2. **Click "Create App"**
3. **Connect GitHub Repository**
4. **Configure:**
   ```
   Type: Web Service
   Source: GitHub (select your repo)
   Branch: main
   Dockerfile: Use existing Dockerfile
   HTTP Port: 8000
   HTTP Request Routes: /
   Health Check: /health
   ```

5. **Add Environment Variables** (same as Render)

6. **Select Plan:**
   - **Basic:** $5/month (512 MB RAM, always on)
   - **Professional:** $12/month (1 GB RAM)

7. **Click "Create Resources"**

**✅ Done!** Your backend will be at: `https://hygiaai-backend-xxx.ondigitalocean.app`

### DigitalOcean Advantages:
- ✅ Simple pricing
- ✅ Always-on (no sleeping)
- ✅ Good performance
- ✅ Docker support

---

## 🚀 Option 5: AWS App Runner (Simplest AWS Option)

**Best for:** AWS ecosystem, simple container deployment

### Quick Setup:

1. **Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner)**
2. **Click "Create service"**
3. **Source:**
   - Select "Container registry" → "Amazon ECR Public"
   - Or connect GitHub and use Dockerfile
4. **Configure:**
   ```
   Service name: hygiaai-backend
   Port: 8000
   Health check: /health
   ```
5. **Add Environment Variables**
6. **Deploy**

**✅ Done!** Your backend will be at: `https://xxx.us-east-1.awsapprunner.com`

---

## 📊 Quick Comparison

| Platform | Free Tier | Ease | Speed | Best For |
|----------|-----------|------|-------|----------|
| **Render** | ✅ 750 hrs | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Easiest alternative |
| **Fly.io** | ✅ 3 VMs | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Global distribution |
| **Cloud Run** | ✅ 2M req | ⭐⭐⭐ | ⭐⭐⭐⭐ | Pay-per-use |
| **DigitalOcean** | ❌ $5/mo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Always-on |
| **App Runner** | ❌ Pay | ⭐⭐⭐ | ⭐⭐⭐⭐ | AWS ecosystem |

---

## 🎯 Recommendation

**For quickest deployment:** Use **Render** - it's the closest to Railway and easiest to set up.

**For best performance:** Use **Fly.io** - global edge network, very fast.

**For cost optimization:** Use **Cloud Run** - pay only for what you use.

---

## 🔧 What You Need to Change

### For Render/Fly.io/Cloud Run:

**No code changes needed!** Your existing setup works:
- ✅ `Dockerfile` - Already optimized
- ✅ `start_server.py` - Works on all platforms
- ✅ `/health` endpoint - Already configured
- ✅ Environment variables - Same format

### Only Change Required:

Update your frontend's `VITE_API_BASE_URL` to point to the new backend URL.

---

## 🚀 Quick Start: Render (Recommended)

1. Go to https://dashboard.render.com
2. New → Web Service
3. Connect GitHub
4. Set:
   - Build: `pip install -r requirements.txt`
   - Start: `python start_server.py`
5. Add environment variables
6. Deploy!

**That's it!** Render will handle everything else automatically.

