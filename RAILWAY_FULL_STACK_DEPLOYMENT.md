# Railway Full-Stack Deployment Guide

Deploy both frontend and backend together on Railway in a single service.

## 🎯 Overview

This guide shows how to deploy the entire HygiaAI application (frontend + backend) as a single Railway service. The FastAPI backend will serve both the API and the React frontend static files.

## ✅ Benefits

- ✅ **Single Service** - One deployment, one URL, easier management
- ✅ **No CORS Issues** - Frontend and backend on same domain
- ✅ **Cost Effective** - Only one Railway service needed
- ✅ **Simpler Configuration** - No need to configure separate frontend/backend URLs

## 📋 Prerequisites

1. Railway account ([railway.app](https://railway.app))
2. GitHub repository with your code
3. Environment variables ready (see below)

## 🚀 Deployment Steps

### Step 1: Update Railway Configuration

The `railway.json` and `Dockerfile` are already configured for full-stack deployment. The Dockerfile will:
1. Build the frontend (React + Vite)
2. Build the backend (Python + FastAPI)
3. Serve both from the same FastAPI server

### Step 2: Configure Railway Project

1. **Go to Railway Dashboard** → [railway.app](https://railway.app)
2. **Create New Project** → "Deploy from GitHub repo"
3. **Select your repository**
4. **Railway will auto-detect** the Dockerfile

### Step 3: Set Environment Variables

In Railway Dashboard → Your Service → Variables, add:

#### Required Backend Variables:
```
DEEPGRAM_API_KEY=your_deepgram_api_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
PORT=8000
```

#### Optional LLM Variables:
```
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

#### Frontend Variables (for build):
```
VITE_API_BASE_URL=/api/v1
NODE_ENV=production
```

**Note:** `VITE_API_BASE_URL` should be `/api/v1` (relative path) since frontend and backend are on the same domain.

### Step 4: Deploy

1. Railway will automatically:
   - Build frontend (npm install + npm run build)
   - Build backend (pip install + copy files)
   - Start FastAPI server
   - Serve frontend from `/` and API from `/api/v1`

2. **Wait for deployment** (usually 3-5 minutes for first build)

3. **Get your URL** from Railway Dashboard → Settings → Networking

## 🔧 How It Works

### Architecture

```
Railway Service
├── FastAPI Backend (Port $PORT)
│   ├── /api/v1/* → API endpoints
│   ├── /docs → API documentation
│   ├── /health → Health check
│   └── /* → Frontend static files (SPA routing)
└── Frontend (Built and served as static files)
    └── React app served from /frontend/dist
```

### Request Flow

1. **API Requests** (`/api/v1/*`):
   - Handled by FastAPI routers
   - Processed by backend logic

2. **Frontend Routes** (`/`, `/dashboard`, `/timeline`, etc.):
   - Served as static files from `/frontend/dist`
   - React Router handles client-side routing
   - Falls back to `index.html` for SPA routing

3. **Static Assets** (`/assets/*`):
   - Served directly from `/frontend/dist/assets`
   - Cached for performance

## 📝 Frontend API Configuration

The frontend is built with `VITE_API_BASE_URL=/api/v1`, which means:

- **Development**: Uses `http://localhost:8000` (from `.env`)
- **Production**: Uses `/api/v1` (relative path, same domain)

This ensures API calls work correctly in both environments.

## 🧪 Testing Deployment

### 1. Test Health Check
```bash
curl https://your-app.railway.app/health
```
Should return: `{"status":"healthy","service":"HygiaAI API","version":"1.0.0"}`

### 2. Test Frontend
Visit: `https://your-app.railway.app`
- Should load the React app
- No CORS errors in console

### 3. Test API
Visit: `https://your-app.railway.app/docs`
- Should show FastAPI documentation
- Try a test endpoint

### 4. Test Frontend → API Communication
- Open browser DevTools → Network tab
- Use the frontend (e.g., search cases)
- Verify API calls go to `/api/v1/...` and succeed

## 🔄 Updating Deployment

### Update Code
1. Push changes to GitHub
2. Railway auto-deploys (if auto-deploy enabled)
3. Or manually trigger deployment in Railway dashboard

### Update Environment Variables
1. Go to Railway Dashboard → Variables
2. Add/Edit variables
3. Railway auto-redeploys

## 🐛 Troubleshooting

### Issue: Frontend Not Loading

**Symptoms:** Blank page or 404 errors

**Solutions:**
1. Check Railway build logs - ensure frontend built successfully
2. Verify `frontend/dist` exists in Docker image
3. Check FastAPI logs for static file serving errors
4. Ensure `VITE_API_BASE_URL` is set correctly

### Issue: API Calls Failing

**Symptoms:** Network errors in browser console

**Solutions:**
1. Check `VITE_API_BASE_URL` is `/api/v1` (relative path)
2. Verify backend is running (check `/health` endpoint)
3. Check Railway logs for backend errors
4. Ensure API routes are prefixed with `/api/v1`

### Issue: Build Fails

**Symptoms:** Railway deployment fails

**Solutions:**
1. Check build logs in Railway dashboard
2. Verify Node.js version (should be 20+)
3. Check frontend dependencies install correctly
4. Verify Python dependencies install correctly
5. Check Dockerfile syntax

### Issue: Slow First Load

**Symptoms:** First page load takes a long time

**Solutions:**
1. This is normal - PyTorch/transformers take time to load
2. Health check has 120s start-period to account for this
3. Subsequent requests will be faster

## 📊 Monitoring

### Railway Dashboard
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: Deployment history and status

### Application Logs
- Backend logs: Railway Dashboard → Deployments → View Logs
- Frontend errors: Browser console (F12)

## 🔐 Security Considerations

1. **Environment Variables**: Never commit API keys
2. **HTTPS**: Railway provides HTTPS automatically
3. **CORS**: Not needed (same domain), but can configure if needed
4. **Rate Limiting**: Consider adding rate limiting for production

## 💰 Cost Optimization

### Free Tier Limits
- **512 MB RAM** (may need upgrade for PyTorch)
- **$5 credit/month** (usually enough for demos)
- **Unlimited deployments**

### Upgrade If Needed
- If you hit memory limits, upgrade to Hobby plan ($5/month)
- Provides 1 GB RAM (sufficient for most use cases)

## 🎉 Success Checklist

- [ ] Frontend loads at root URL (`/`)
- [ ] API documentation accessible at `/docs`
- [ ] Health check passes at `/health`
- [ ] Frontend can call API endpoints
- [ ] No CORS errors in browser console
- [ ] Static assets load correctly
- [ ] SPA routing works (navigate between pages)

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Vite Build Guide](https://vitejs.dev/guide/build.html)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

## 🔄 Alternative: Separate Services

If you prefer separate frontend/backend services:

1. **Backend Service**: Use current setup (backend only)
2. **Frontend Service**: 
   - Create new Railway service
   - Use `frontend/` as root directory
   - Set build command: `npm run build`
   - Set start command: `npx serve -s dist -p $PORT`
   - Set `VITE_API_BASE_URL` to backend URL

See `FRONTEND_DEPLOYMENT_RAILWAY.md` for separate deployment guide.

---

**Your full-stack app is now live on Railway! 🚀**

