# Qdrant Cloud Deployment Guide

Multiple options to deploy Qdrant in the cloud for your HygiaAI application.

---

## 🎯 Option 1: Qdrant Cloud (Recommended - Easiest)

**Best for:** Production, managed service, easiest setup

### Steps:

1. **Sign up at [Qdrant Cloud](https://cloud.qdrant.io)**
   - Free tier: 1GB storage
   - Paid plans: More storage and better performance

2. **Create a Cluster:**
   - Click "Create Cluster"
   - Choose region (closest to your backend)
   - Select plan (Free tier is fine for demos)

3. **Get Connection Details:**
   - Host: `your-cluster-name.qdrant.io`
   - Port: `6333`
   - API Key: (provided in dashboard)

4. **Update Railway Environment Variables:**
   ```
   QDRANT_HOST=your-cluster-name.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_api_key_here
   ```

**Pros:**
- ✅ Fully managed (no maintenance)
- ✅ Automatic backups
- ✅ High availability
- ✅ Free tier available
- ✅ Easy to scale

**Cons:**
- ❌ Costs money for larger deployments
- ❌ Less control over configuration

---

## 🚂 Option 2: Railway Docker Service (Recommended for Free Tier)

**Best for:** Free tier, same platform as backend, easy setup

### Steps:

1. **In Railway Dashboard:**
   - Click "New" → "Empty Service"
   - Or "New" → "GitHub Repo" → Select "Deploy from Dockerfile"

2. **Create `Dockerfile.qdrant` in your repo:**
   ```dockerfile
   FROM qdrant/qdrant:latest
   
   EXPOSE 6333
   EXPOSE 6334
   ```

3. **Or use Railway's Docker Image option:**
   - Service Type: **Docker**
   - Docker Image: `qdrant/qdrant:latest`
   - Port: `6333`

4. **Configure Service:**
   - **Port:** `6333`
   - **Public Networking:** Enabled
   - **Generate Domain:** Click to get URL

5. **Add Volume (for persistence):**
   - Railway automatically creates volumes
   - Data persists across deployments

6. **Get Connection Details:**
   - Railway provides: `https://your-qdrant.railway.app`
   - Extract hostname: `your-qdrant.railway.app`
   - Port: `6333` (or check Railway port mapping)

7. **Update Backend Environment Variables:**
   ```
   QDRANT_HOST=your-qdrant.railway.app
   QDRANT_PORT=6333
   QDRANT_API_KEY= (leave empty if no auth)
   ```

**Pros:**
- ✅ Free tier available
- ✅ Same platform as backend
- ✅ Easy to manage
- ✅ Automatic deployments

**Cons:**
- ❌ Less control than self-hosted
- ❌ Railway-specific

---

## 🐳 Option 3: Render Docker Service

**Best for:** Alternative to Railway, free tier available

### Steps:

1. **Go to [Render](https://render.com)**
2. **New → Web Service**
3. **Configure:**
   - **Name:** `hygiaai-qdrant`
   - **Environment:** Docker
   - **Docker Image:** `qdrant/qdrant:latest`
   - **Port:** `6333`
   - **Plan:** Free (or paid)

4. **Add Environment Variables:**
   ```
   QDRANT__SERVICE__HTTP_PORT=6333
   QDRANT__SERVICE__GRPC_PORT=6334
   ```

5. **Get URL:**
   - Render provides: `https://hygiaai-qdrant.onrender.com`
   - Use hostname: `hygiaai-qdrant.onrender.com`

6. **Update Backend:**
   ```
   QDRANT_HOST=hygiaai-qdrant.onrender.com
   QDRANT_PORT=6333
   ```

**Pros:**
- ✅ Free tier available
- ✅ Easy Docker deployment
- ✅ Persistent storage

**Cons:**
- ❌ Free tier spins down after inactivity
- ❌ Slower cold starts

---

## ✈️ Option 4: Fly.io (Global Distribution)

**Best for:** Global distribution, low latency

### Steps:

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create `fly.toml`:**
   ```toml
   app = "hygiaai-qdrant"
   primary_region = "iad"
   
   [build]
     image = "qdrant/qdrant:latest"
   
   [[services]]
     internal_port = 6333
     protocol = "tcp"
     
     [[services.ports]]
       port = 6333
       handlers = ["tcp"]
   ```

4. **Deploy:**
   ```bash
   fly launch
   fly deploy
   ```

5. **Get URL:**
   - Fly provides: `hygiaai-qdrant.fly.dev`
   - Update backend with this hostname

**Pros:**
- ✅ Global edge network
- ✅ Low latency
- ✅ Good free tier

**Cons:**
- ❌ More complex setup
- ❌ CLI required

---

## 🐙 Option 5: DigitalOcean App Platform

**Best for:** Simple Docker hosting

### Steps:

1. **Go to DigitalOcean App Platform**
2. **Create App → Docker Hub**
3. **Configure:**
   - **Image:** `qdrant/qdrant:latest`
   - **Port:** `6333`
   - **Plan:** Basic ($5/month)

4. **Deploy and get URL**

**Pros:**
- ✅ Simple interface
- ✅ Good documentation

**Cons:**
- ❌ Paid only (no free tier)
- ❌ More expensive

---

## 📋 Quick Comparison

| Option | Cost | Setup Difficulty | Best For |
|--------|------|------------------|----------|
| **Qdrant Cloud** | Free tier + paid | ⭐ Easy | Production |
| **Railway** | Free tier | ⭐⭐ Medium | Same platform |
| **Render** | Free tier | ⭐⭐ Medium | Alternative |
| **Fly.io** | Free tier | ⭐⭐⭐ Hard | Global |
| **DigitalOcean** | Paid | ⭐⭐ Medium | Simple |

---

## 🔧 Recommended Setup: Railway Docker Service

Since you're already using Railway, here's the detailed setup:

### Step-by-Step:

1. **In Railway Dashboard:**
   - Click "New" → "Empty Service"

2. **Configure Service:**
   - **Name:** `hygiaai-qdrant`
   - **Source:** Docker Image
   - **Image:** `qdrant/qdrant:latest`

3. **Settings:**
   - **Port:** `6333`
   - **Public Networking:** ✅ Enabled
   - **Generate Domain:** Click to get URL

4. **Add Volume (Optional but Recommended):**
   - Railway automatically handles persistence
   - Data stored in Railway's volume system

5. **Get Connection Info:**
   - Railway provides domain like: `hygiaai-qdrant-production.up.railway.app`
   - Note the hostname (without `https://`)

6. **Update Backend Environment Variables:**
   ```
   QDRANT_HOST=hygiaai-qdrant-production.up.railway.app
   QDRANT_PORT=6333
   QDRANT_API_KEY= (leave empty, Railway doesn't require auth by default)
   ```

7. **Test Connection:**
   ```bash
   curl https://hygiaai-qdrant-production.up.railway.app:6333/health
   ```
   Should return: `{"status":"ok"}`

---

## 🔐 Security Considerations

### For Production:

1. **Enable Authentication:**
   - Qdrant Cloud: Built-in API keys
   - Self-hosted: Set `QDRANT_API_KEY` environment variable

2. **Use HTTPS:**
   - Railway/Render provide HTTPS automatically
   - Qdrant Cloud uses HTTPS

3. **Restrict Access:**
   - Use private networking if available
   - Whitelist backend IP addresses

---

## 📊 Migration from Local Qdrant

If you have data in local Qdrant:

1. **Export Data:**
   ```bash
   # Create snapshot
   curl -X POST http://localhost:6333/collections/{collection_name}/snapshots
   ```

2. **Upload to Cloud:**
   - Use Qdrant Cloud dashboard
   - Or use Qdrant client to re-index

3. **Re-populate:**
   ```bash
   # Update env vars to point to cloud
   export QDRANT_HOST=your-cloud-host
   export QDRANT_API_KEY=your_key
   
   # Re-run population scripts
   python scripts/populate_extended_demo_data.py
   python scripts/populate_knowledge_base_complete.py
   ```

---

## ✅ Verification

After deployment, verify Qdrant is accessible:

```bash
# Health check
curl https://your-qdrant-host:6333/health

# List collections
curl https://your-qdrant-host:6333/collections
```

---

## 🎯 Recommended: Railway Docker Service

**Why Railway:**
- ✅ Same platform as your backend
- ✅ Free tier available
- ✅ Easy to manage
- ✅ Automatic HTTPS
- ✅ Persistent volumes
- ✅ Same dashboard

**Quick Setup:**
1. Railway → New → Empty Service
2. Docker Image: `qdrant/qdrant:latest`
3. Port: `6333`
4. Public Networking: Enabled
5. Generate Domain
6. Update backend env vars
7. Done! 🎉

---

**Need Help?** Check Railway logs or Qdrant documentation at [qdrant.tech](https://qdrant.tech)

