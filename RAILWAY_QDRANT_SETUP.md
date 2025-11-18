# Railway Qdrant Setup - Step by Step

Quick guide to deploy Qdrant on Railway alongside your backend.

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Qdrant Service in Railway

1. **Go to Railway Dashboard**
2. **Click "New" → "Empty Service"**
3. **Name it:** `hygiaai-qdrant`

### Step 2: Configure Docker Image

1. **In the service settings, find "Deploy" section**
2. **Click "Deploy from Docker Hub"** or **"Deploy from Image"**
3. **Enter Docker Image:** `qdrant/qdrant:latest`
4. **Click "Deploy"**

### Step 3: Configure Networking

1. **Go to "Networking" tab**
2. **Enable "Public Networking"**
3. **Click "Generate Domain"**
4. **Copy the domain** (e.g., `hygiaai-qdrant-production.up.railway.app`)

### Step 4: Set Port

1. **Go to "Settings" tab**
2. **Find "Port" setting**
3. **Set to:** `6333`
4. **Save**

### Step 5: Update Backend Environment Variables

1. **Go to your backend service in Railway**
2. **Click "Variables" tab**
3. **Add/Update:**
   ```
   QDRANT_HOST=hygiaai-qdrant-production.up.railway.app
   QDRANT_PORT=6333
   ```
   (Replace with your actual Qdrant domain)

4. **Save**

### Step 6: Verify

1. **Wait for Qdrant to deploy** (takes ~2 minutes)
2. **Test health endpoint:**
   ```bash
   curl https://your-qdrant-domain.railway.app/health
   ```
   Should return: `{"status":"ok"}`

3. **Check Railway logs** to ensure Qdrant started successfully

---

## 🔧 Alternative: Using Railway Config File

If you prefer config-as-code:

1. **Create `railway-qdrant.json`:**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile.qdrant"
     },
     "deploy": {
       "startCommand": "",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. **Create `Dockerfile.qdrant`:**
   ```dockerfile
   FROM qdrant/qdrant:latest
   
   EXPOSE 6333
   EXPOSE 6334
   ```

3. **Deploy using this config**

---

## 📊 Railway Qdrant Configuration

### Recommended Settings:

- **CPU:** 0.5 vCPU (free tier) or 1 vCPU
- **Memory:** 512 MB (free tier) or 1 GB
- **Port:** `6333`
- **Public Networking:** ✅ Enabled
- **Restart Policy:** On Failure
- **Healthcheck:** `/health` (automatic)

### Environment Variables (Optional):

```
QDRANT__SERVICE__HTTP_PORT=6333
QDRANT__SERVICE__GRPC_PORT=6334
QDRANT_API_KEY=your_secret_key (optional, for auth)
```

---

## 🔗 Connecting Backend to Railway Qdrant

### Update Backend Environment Variables:

In your backend Railway service, set:

```
QDRANT_HOST=your-qdrant-service.railway.app
QDRANT_PORT=6333
QDRANT_API_KEY= (leave empty if no auth)
```

**Note:** Railway automatically handles HTTPS, so use the domain Railway provides.

---

## 🧪 Testing Connection

### From Backend:

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    host=os.getenv("QDRANT_HOST"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
    api_key=os.getenv("QDRANT_API_KEY") or None
)

# Test connection
collections = client.get_collections()
print(f"Connected! Collections: {collections}")
```

### From Command Line:

```bash
# Health check
curl https://your-qdrant.railway.app/health

# List collections
curl https://your-qdrant.railway.app/collections
```

---

## 💾 Data Persistence

Railway automatically creates volumes for Docker services. Your Qdrant data will persist across deployments.

**To backup:**
- Use Qdrant snapshots
- Or export data via API

---

## 🔄 Updating Qdrant

Railway will automatically pull the latest `qdrant/qdrant:latest` image when you redeploy.

**To update:**
1. Go to Qdrant service
2. Click "Redeploy"
3. Railway pulls latest image

---

## 🐛 Troubleshooting

### Qdrant Not Starting

**Check logs:**
- Railway Dashboard → Qdrant Service → Logs
- Look for errors

**Common issues:**
- Port conflict: Ensure port 6333 is set correctly
- Memory: Increase memory allocation if needed

### Backend Can't Connect

**Verify:**
1. Qdrant is running (check logs)
2. Public networking is enabled
3. Domain is correct in backend env vars
4. Port is `6333`

**Test:**
```bash
curl https://your-qdrant.railway.app/health
```

### Data Not Persisting

Railway volumes persist automatically. If data is lost:
- Check Railway volume settings
- Verify service wasn't deleted and recreated

---

## ✅ Checklist

- [ ] Qdrant service created in Railway
- [ ] Docker image: `qdrant/qdrant:latest`
- [ ] Port set to `6333`
- [ ] Public networking enabled
- [ ] Domain generated
- [ ] Backend env vars updated
- [ ] Health check passes
- [ ] Backend can connect

---

## 🎉 Done!

Your Qdrant is now running in the cloud on Railway!

**Next Steps:**
1. Populate demo data (point scripts to cloud Qdrant)
2. Test backend connection
3. Verify data persistence
4. Monitor usage in Railway dashboard

---

**Cost:** Free tier includes 512MB RAM, sufficient for demos and small projects.

