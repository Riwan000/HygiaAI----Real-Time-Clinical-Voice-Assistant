# Frontend Deployment Guide (After Railway Backend)

Complete step-by-step guide to deploy the HygiaAI frontend after your backend is deployed on Railway.

## 📋 Prerequisites

1. ✅ **Backend deployed on Railway** (you should have your Railway backend URL)
2. ✅ **GitHub repository** with your code pushed
3. ✅ **Vercel account** (free tier is sufficient) - Sign up at [vercel.com](https://vercel.com)

---

## 🚀 Quick Deployment (Recommended: Vercel Dashboard)

### Step 1: Get Your Backend URL from Railway

1. Go to your Railway dashboard: [railway.app](https://railway.app)
2. Click on your backend service
3. Go to the **"Settings"** tab
4. Under **"Networking"**, find your **"Public Domain"**
   - Example: `https://your-backend-name.up.railway.app`
5. **Copy this URL** - you'll need it for the frontend environment variable

### Step 2: Deploy Frontend to Vercel

#### Option A: Via Vercel Dashboard (Easiest)

1. **Go to Vercel Dashboard:**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Sign in with GitHub (if not already)

2. **Add New Project:**
   - Click **"Add New..."** → **"Project"**
   - Import your GitHub repository
   - Select the repository containing your HygiaAI project

3. **Configure Project Settings:**
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

4. **Add Environment Variables:**
   Click **"Environment Variables"** and add:
   
   ```
   Name: VITE_API_BASE_URL
   Value: https://your-backend-name.up.railway.app
   
   Name: NODE_ENV
   Value: production
   ```
   
   ⚠️ **Important:** Replace `your-backend-name.up.railway.app` with your actual Railway backend URL

5. **Deploy:**
   - Click **"Deploy"**
   - Wait 1-2 minutes for build to complete
   - Your frontend will be live at: `https://your-project.vercel.app`

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy (preview first)
vercel

# Set environment variable
vercel env add VITE_API_BASE_URL production
# When prompted, enter: https://your-backend-name.up.railway.app

# Deploy to production
vercel --prod
```

---

## 🔧 Configuration Details

### Environment Variables Required

Add these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_BASE_URL` | `https://your-backend.railway.app` | Your Railway backend URL |
| `NODE_ENV` | `production` | Production environment flag |

### Optional Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_DEEPGRAM_API_KEY` | `your_key` | For transcription features |
| `VITE_ENABLE_OFFLINE_MODE` | `true` | Enable offline functionality |
| `VITE_ENABLE_FEDERATED_LEARNING` | `false` | Enable federated learning |

---

## ✅ Post-Deployment Checklist

### 1. Verify Frontend is Live

- Visit your Vercel URL: `https://your-project.vercel.app`
- Check that the page loads without errors

### 2. Test Backend Connection

- Open browser DevTools (F12)
- Go to **Network** tab
- Try using a feature that calls the backend (e.g., search cases)
- Verify API calls are going to your Railway backend URL

### 3. Check CORS Configuration

If you see CORS errors in the browser console:

1. Go to Railway dashboard → Your backend service → Settings
2. Add environment variable:
   ```
   ALLOWED_ORIGINS=https://your-project.vercel.app,http://localhost:3000
   ```
3. Redeploy the backend (Railway auto-redeploys on env var changes)

### 4. Test Key Features

- ✅ Dashboard loads cases
- ✅ Multimodal input form works
- ✅ Timeline displays patient data
- ✅ Analytics shows charts
- ✅ Knowledge base browser works

---

## 🔄 Updating Backend URL

If you need to change the backend URL later:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Edit `VITE_API_BASE_URL`
3. Redeploy (Vercel will auto-redeploy, or click "Redeploy" button)

---

## 🐛 Troubleshooting

### Issue: "Network Error" or "Failed to fetch"

**Solution:**
1. Check that `VITE_API_BASE_URL` is set correctly in Vercel
2. Verify your Railway backend is running (check Railway dashboard)
3. Test backend directly: `https://your-backend.railway.app/health`
4. Check CORS settings in Railway backend

### Issue: CORS Errors

**Solution:**
Add to Railway backend environment variables:
```
ALLOWED_ORIGINS=https://your-project.vercel.app
```

Then redeploy backend.

### Issue: Frontend Build Fails

**Solution:**
1. Check Vercel build logs for errors
2. Ensure `Root Directory` is set to `frontend`
3. Verify `Build Command` is `npm run build`
4. Check that all dependencies are in `package.json`

### Issue: API Calls Go to Wrong URL

**Solution:**
1. Verify `VITE_API_BASE_URL` environment variable in Vercel
2. Clear browser cache
3. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
4. Check `frontend/src/utils/constants.ts` - should use `import.meta.env.VITE_API_BASE_URL`

---

## 📱 Custom Domain (Optional)

To use your own domain:

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Follow DNS configuration instructions
4. Update `ALLOWED_ORIGINS` in Railway backend to include your custom domain

---

## 🔐 Security Best Practices

1. **Never commit API keys** - Use environment variables only
2. **Use HTTPS** - Both Vercel and Railway provide HTTPS by default
3. **Set CORS properly** - Only allow your frontend domain in Railway backend
4. **Keep dependencies updated** - Regularly update npm packages

---

## 📊 Monitoring

### Vercel Analytics (Optional)

1. Go to Vercel Dashboard → Your Project → Analytics
2. Enable Analytics (free tier available)
3. Monitor page views, performance, and errors

### Railway Logs

- View backend logs in Railway Dashboard → Your Service → Deployments → View Logs
- Monitor API errors and performance

---

## 🎉 Success!

Once deployed, you'll have:

- ✅ **Frontend:** `https://your-project.vercel.app`
- ✅ **Backend:** `https://your-backend.railway.app`
- ✅ **Full Stack:** Connected and working!

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Frontend Deployment Guide](./frontend/DEPLOYMENT.md)
- [Vercel Deployment Guide](./VERCEL_DEPLOYMENT_GUIDE.md)

---

## 🆘 Need Help?

1. Check build logs in Vercel Dashboard
2. Check backend logs in Railway Dashboard
3. Review browser console for errors
4. Verify environment variables are set correctly
5. Test backend health endpoint: `https://your-backend.railway.app/health`

