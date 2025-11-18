# Vercel Deployment Guide - HygiaAI

Complete guide to deploy HygiaAI frontend to Vercel.

## ✅ What Can Be Deployed to Vercel

- ✅ **Frontend (React + Vite)** → Perfect for Vercel
- ❌ **Backend (FastAPI)** → Use Railway/Render instead (see below)

---

## 🚀 Quick Deployment (3 Methods)

### Method 1: Vercel Dashboard (Easiest - Recommended)

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

3. **Click "Add New Project"**

4. **Import GitHub Repository:**
   - Select your repository
   - Click "Import"

5. **Configure Project Settings:**
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

6. **Add Environment Variables:**
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   NODE_ENV=production
   ```
   ⚠️ **Important:** Replace `your-backend-url.railway.app` with your actual backend URL

7. **Click "Deploy"**

8. **Wait for deployment** (usually 1-2 minutes)

9. **Your app is live!** → `https://your-project.vercel.app`

---

### Method 2: Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy (preview)
vercel

# Deploy to production
vercel --prod

# Set environment variables
vercel env add VITE_API_BASE_URL production
# Enter: https://your-backend-url.railway.app
```

---

### Method 3: GitHub Integration (Automatic)

1. **Connect GitHub to Vercel:**
   - Go to Vercel Dashboard → Settings → Git
   - Connect your GitHub account
   - Select your repository

2. **Configure Auto-Deploy:**
   - Every push to `main` → Production deployment
   - Pull requests → Preview deployments

3. **Set Environment Variables:**
   - Go to Project Settings → Environment Variables
   - Add `VITE_API_BASE_URL` for Production, Preview, and Development

4. **Push to trigger deployment:**
   ```bash
   git push origin main
   ```

---

## ⚙️ Backend Deployment (Required)

Since Vercel only hosts the frontend, you need to deploy the backend separately:

### Option A: Railway (Recommended)

1. **Go to [Railway](https://railway.app)**
2. **New Project → Deploy from GitHub**
3. **Select your repository**
4. **Configure:**
   - Root Directory: `.` (project root)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables:**
   ```
   DEEPGRAM_API_KEY=your_key
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_key
   GOOGLE_API_KEY=your_key
   PORT=8000
   ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:3000
   ```
6. **Get your backend URL:** `https://your-app.railway.app`

### Option B: Render

1. **Go to [Render](https://render.com)**
2. **New → Web Service**
3. **Connect GitHub repository**
4. **Configure:**
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. **Add same environment variables as Railway**

---

## 🔧 Configuration Files

### `frontend/vercel.json` (Already exists)

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

This file is already configured correctly!

---

## 📋 Environment Variables Checklist

### Frontend (Vercel)

- [ ] `VITE_API_BASE_URL` - Your backend URL (e.g., `https://your-app.railway.app`)
- [ ] `NODE_ENV` - Set to `production`

### Backend (Railway/Render)

- [ ] `DEEPGRAM_API_KEY` - For transcription
- [ ] `QDRANT_URL` - Qdrant Cloud URL
- [ ] `QDRANT_API_KEY` - Qdrant API key
- [ ] `GOOGLE_API_KEY` - For Gemini LLM
- [ ] `ALLOWED_ORIGINS` - Your Vercel frontend URL
- [ ] `PORT` - Usually `8000` (Railway auto-sets this)

---

## 🧪 Testing Deployment

### 1. Test Frontend

```bash
# Visit your Vercel URL
https://your-project.vercel.app

# Check browser console for errors
# Verify API calls are going to correct backend URL
```

### 2. Test Backend

```bash
# Health check
curl https://your-backend.railway.app/health

# API docs
https://your-backend.railway.app/docs
```

### 3. Test Integration

1. Open frontend: `https://your-project.vercel.app`
2. Try uploading patient data
3. Check browser Network tab for API calls
4. Verify responses are successful

---

## 🔍 Troubleshooting

### Issue: Frontend can't connect to backend

**Solution:**
1. Check `VITE_API_BASE_URL` in Vercel environment variables
2. Verify backend is running (check Railway/Render logs)
3. Check CORS settings in backend (`ALLOWED_ORIGINS`)
4. Check browser console for CORS errors

### Issue: Build fails on Vercel

**Solution:**
1. Check build logs in Vercel dashboard
2. Verify Node.js version (should be 18+)
3. Check `package.json` scripts are correct
4. Ensure `frontend/vercel.json` exists

### Issue: Environment variables not working

**Solution:**
1. Variables must start with `VITE_` to be accessible in frontend
2. Redeploy after adding variables
3. Check variable names match exactly

### Issue: 404 errors on page refresh

**Solution:**
- Already handled by `vercel.json` rewrites
- If still happening, check SPA routing configuration

---

## 📊 Deployment Status

After deployment, you should have:

- ✅ Frontend: `https://your-project.vercel.app`
- ✅ Backend: `https://your-backend.railway.app`
- ✅ API Docs: `https://your-backend.railway.app/docs`
- ✅ Health Check: `https://your-backend.railway.app/health`

---

## 🎯 Next Steps

1. **Deploy Backend First** (Railway/Render)
   - Get backend URL
   - Test API endpoints

2. **Deploy Frontend** (Vercel)
   - Set `VITE_API_BASE_URL` to backend URL
   - Deploy

3. **Update CORS** in backend
   - Add Vercel URL to `ALLOWED_ORIGINS`

4. **Test Everything**
   - Upload patient data
   - Test transcription
   - Test knowledge base search

5. **Share Your App!**
   - Share Vercel frontend URL
   - Monitor logs in Railway/Render dashboard

---

## 💡 Pro Tips

1. **Use Preview Deployments:**
   - Every PR gets a preview URL
   - Test before merging to main

2. **Monitor Logs:**
   - Vercel: Dashboard → Deployments → Logs
   - Railway: Dashboard → Deployments → Logs

3. **Set Up Custom Domain:**
   - Vercel: Settings → Domains
   - Add your custom domain

4. **Enable Analytics:**
   - Vercel Analytics (free tier)
   - Monitor performance

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html)

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Backend deployed to Railway/Render
- [ ] Backend URL obtained
- [ ] Frontend deployed to Vercel
- [ ] Environment variables set in Vercel
- [ ] CORS configured in backend
- [ ] Health check passes
- [ ] Frontend loads correctly
- [ ] API calls work
- [ ] All features tested

---

**Your app is now live and ready to share! 🎉**

