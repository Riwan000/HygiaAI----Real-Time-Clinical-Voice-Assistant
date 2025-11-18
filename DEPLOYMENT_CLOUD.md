# Cloud Deployment Guide - HygiaAI

Complete guide to deploy HygiaAI to cloud platforms and share with others.

## 🏗️ Architecture Overview

HygiaAI consists of three main components:

1. **Frontend** (React + Vite) → Deploy to **Vercel** (recommended)
2. **Backend** (FastAPI + Python) → Deploy to **Railway** or **Render**
3. **Database** (Qdrant Vector DB) → Use **Qdrant Cloud** or self-hosted

---

## 📋 Prerequisites

- GitHub account (for repository hosting)
- Vercel account (free tier available)
- Railway/Render account (for backend)
- Qdrant Cloud account (free tier available) OR Docker hosting
- API Keys:
  - Deepgram API key ([Get here](https://console.deepgram.com))
  - Optional: Google Gemini API key ([Get here](https://makersuite.google.com/app/apikey))

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/hygiaai.git
   git push -u origin main
   ```

2. **Ensure `.env` is in `.gitignore`:**
   ```bash
   # Check .gitignore includes:
   .env
   .env.local
   .env.production
   ```

---

## 🎨 Step 2: Deploy Frontend to Vercel

### Option A: Vercel Dashboard (Easiest)

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
2. **Click "Add New Project"**
3. **Import your GitHub repository**
4. **Configure Project Settings:**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

5. **Add Environment Variables:**
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   NODE_ENV=production
   ```

6. **Click "Deploy"**

### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Navigate to frontend directory
cd frontend

# Deploy
vercel

# For production
vercel --prod
```

### Option C: GitHub Integration (Automatic)

1. Connect GitHub repo to Vercel
2. Configure environment variables in Vercel dashboard
3. Every push to `main` auto-deploys to production
4. Pull requests create preview deployments

**Your frontend will be live at:** `https://your-project.vercel.app`

---

## ⚙️ Step 3: Deploy Backend

### Option A: Railway (Recommended - Easy)

1. **Go to [Railway](https://railway.app)**
2. **Click "New Project" → "Deploy from GitHub repo"**
3. **Select your repository**
4. **Configure Settings:**
   - **Root Directory:** Leave empty (project root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_server.py` or `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables:**
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   QDRANT_HOST=your-qdrant-host.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_qdrant_api_key
   OPENAI_API_KEY=your_openai_key (optional)
   PORT=8000
   ```

6. **Generate Domain:** Railway auto-generates a URL like `your-app.railway.app`

### Option B: Render (Alternative)

1. **Go to [Render](https://render.com)**
2. **Click "New" → "Web Service"**
3. **Connect GitHub repository**
4. **Configure:**
   - **Name:** hygiaai-backend
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or paid for better performance)

5. **Add Environment Variables** (same as Railway)

### Option C: Fly.io (For Global Distribution)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize (in project root)
fly launch

# Deploy
fly deploy
```

**Your backend will be live at:** `https://your-backend.railway.app` (or render/fly URL)

---

## 🗄️ Step 4: Set Up Qdrant Database

### Option A: Qdrant Cloud (Recommended - Free Tier Available)

1. **Sign up at [Qdrant Cloud](https://cloud.qdrant.io)**
2. **Create a new cluster** (Free tier: 1GB storage)
3. **Get connection details:**
   - Host: `your-cluster.qdrant.io`
   - Port: `6333`
   - API Key: (provided in dashboard)

4. **Update backend environment variables:**
   ```
   QDRANT_HOST=your-cluster.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_api_key
   ```

### Option B: Self-Hosted Qdrant (Railway/Render)

1. **Create a new service** in Railway/Render
2. **Use Docker image:** `qdrant/qdrant:latest`
3. **Expose port:** `6333`
4. **Add volume** for persistence (Railway/Render handle this)

### Option C: Docker on VPS (DigitalOcean, AWS, etc.)

```bash
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

---

## 🔗 Step 5: Connect Frontend to Backend

1. **Update frontend environment variables in Vercel:**
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```

2. **Update backend CORS settings** (`src/api/main.py`):
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://your-project.vercel.app",
           "http://localhost:3000"  # For local testing
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Redeploy both services**

---

## 📊 Step 6: Populate Demo Data

After deployment, populate demo data:

### Option A: Run Locally (Connect to Cloud DB)

1. **Set environment variables locally:**
   ```bash
   export QDRANT_HOST=your-cluster.qdrant.io
   export QDRANT_PORT=6333
   export QDRANT_API_KEY=your_api_key
   ```

2. **Run population scripts:**
   ```bash
   python scripts/populate_extended_demo_data.py
   python scripts/populate_knowledge_base_complete.py
   ```

### Option B: Create API Endpoint for Data Population

Add a protected admin endpoint in your backend to populate data via API.

---

## ✅ Step 7: Verify Deployment

### Check Frontend:
- ✅ Visit: `https://your-project.vercel.app`
- ✅ Should load without errors
- ✅ Check browser console for API connection

### Check Backend:
- ✅ Visit: `https://your-backend.railway.app/health`
- ✅ Should return: `{"status":"healthy","service":"HygiaAI API"}`
- ✅ Visit: `https://your-backend.railway.app/docs` for API docs

### Check Database:
- ✅ Use Qdrant Cloud dashboard or API
- ✅ Verify collections exist: `hygiaai_clinical_cases`, `hygiaai_knowledge_base`

---

## 🔐 Step 8: Environment Variables Summary

### Frontend (Vercel):
```
VITE_API_BASE_URL=https://your-backend.railway.app
NODE_ENV=production
```

### Backend (Railway/Render):
```
DEEPGRAM_API_KEY=your_deepgram_key
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key
GOOGLE_API_KEY=your_google_api_key (optional - for LLM features)
PORT=8000
```

---

## 🌐 Step 9: Share Your Application

### Get Shareable Links:

1. **Frontend URL:** `https://your-project.vercel.app`
2. **Backend API:** `https://your-backend.railway.app`
3. **API Documentation:** `https://your-backend.railway.app/docs`

### Share Options:

- **Direct Link:** Share the Vercel frontend URL
- **Demo Video:** Record a screen share showing features
- **Documentation:** Share this deployment guide

---

## 🎯 Quick Deploy Checklist

- [ ] Code pushed to GitHub
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway/Render
- [ ] Qdrant Cloud cluster created
- [ ] Environment variables configured
- [ ] CORS settings updated
- [ ] Demo data populated
- [ ] Health checks passing
- [ ] Frontend connects to backend
- [ ] Application tested end-to-end

---

## 💰 Cost Estimation (Free Tier)

| Service | Free Tier | Paid Plans |
|---------|-----------|------------|
| **Vercel** | Unlimited projects, 100GB bandwidth | $20/mo for team |
| **Railway** | $5 credit/month | $5+/mo per service |
| **Render** | 750 hours/month | $7+/mo per service |
| **Qdrant Cloud** | 1GB storage | $25+/mo for more |
| **Fly.io** | 3 shared VMs | $1.94+/mo per VM |

**Total Free Tier:** ~$0-5/month for small demos

---

## 🐛 Troubleshooting

### Frontend Not Connecting to Backend

**Issue:** CORS errors in browser console

**Solution:**
1. Check backend CORS settings include frontend URL
2. Verify `VITE_API_BASE_URL` is set correctly
3. Check backend is accessible (visit `/health` endpoint)

### Backend Not Starting

**Issue:** Application crashes on startup

**Solution:**
1. Check logs in Railway/Render dashboard
2. Verify all environment variables are set
3. Check Python version (should be 3.8+)
4. Verify dependencies install correctly

### Database Connection Failed

**Issue:** Backend can't connect to Qdrant

**Solution:**
1. Verify Qdrant host/port are correct
2. Check API key is valid
3. Test connection: `curl https://your-cluster.qdrant.io:6333/health`
4. Check firewall/network settings

### Build Fails

**Issue:** Vercel build fails

**Solution:**
1. Check Node.js version (v22.12+ or v20.19+)
2. Verify `package.json` scripts are correct
3. Check build logs in Vercel dashboard
4. Ensure `vercel.json` is in frontend directory

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## 🎉 Deployment Complete!

Your HygiaAI application is now live and shareable!

**Next Steps:**
1. Test all features
2. Share the frontend URL with others
3. Monitor usage and errors
4. Set up custom domain (optional)
5. Configure analytics (optional)

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0

