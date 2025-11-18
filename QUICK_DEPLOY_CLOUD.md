# Quick Cloud Deployment Guide

**Deploy HygiaAI in 15 minutes using free tiers!**

## 🚀 Quick Start (3 Steps)

### 1. Frontend → Vercel (5 min)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel

# Add environment variable in Vercel dashboard:
# VITE_API_BASE_URL=https://your-backend-url.railway.app
```

**Or use Vercel Dashboard:**
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repo
3. Set Root Directory: `frontend`
4. Add env var: `VITE_API_BASE_URL`
5. Deploy!

---

### 2. Backend → Railway (5 min)

1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables:
   ```
   DEEPGRAM_API_KEY=your_key
   QDRANT_HOST=your-cluster.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_key
   PORT=8000
   ```
5. Railway auto-detects Python and deploys!

**Or use Render:**
- Same process, use `render.yaml` config file

---

### 3. Database → Qdrant Cloud (5 min)

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create free cluster (1GB)
3. Copy connection details
4. Add to backend env vars

---

## ✅ Done!

Your app is live:
- Frontend: `https://your-project.vercel.app`
- Backend: `https://your-app.railway.app`
- API Docs: `https://your-app.railway.app/docs`

---

## 📝 Next Steps

1. **Populate demo data:**
   ```bash
   # Set QDRANT env vars locally
   export QDRANT_HOST=your-cluster.qdrant.io
   export QDRANT_API_KEY=your_key
   
   # Run population scripts
   python scripts/populate_extended_demo_data.py
   python scripts/populate_knowledge_base_complete.py
   ```

2. **Update CORS in backend:**
   - Set `ALLOWED_ORIGINS` env var: `https://your-project.vercel.app`
   - Or edit `src/api/main.py` directly

3. **Share your app!**
   - Share the Vercel frontend URL
   - Test all features
   - Monitor logs in Railway dashboard

---

## 💡 Tips

- **Free tiers are enough** for demos and small projects
- **Vercel** has unlimited projects on free tier
- **Railway** gives $5 credit/month
- **Qdrant Cloud** free tier: 1GB storage

---

## 🐛 Issues?

See full guide: `DEPLOYMENT_CLOUD.md`

