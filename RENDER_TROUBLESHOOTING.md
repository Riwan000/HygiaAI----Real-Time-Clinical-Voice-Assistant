# Render Deployment Troubleshooting

## Issue: ModuleNotFoundError for cryptography

### Solution Applied:

1. ✅ Added `cryptography>=41.0.0` to `requirements.txt`
2. ✅ Added `cryptography>=41.0.0` to Dockerfile installation
3. ✅ Made encryption imports lazy in `src/storage/__init__.py`

### If Still Getting Error:

**Force Render to Rebuild:**

1. **Go to Render Dashboard**
2. **Click on your service**
3. **Go to "Settings" tab**
4. **Click "Clear build cache"**
5. **Go to "Events" tab**
6. **Click "Manual Deploy" → "Deploy latest commit"**

This ensures Render rebuilds from scratch with all new dependencies.

### Alternative: Verify Dockerfile is Being Used

If Render isn't using Dockerfile:

1. **Check Render Dashboard → Settings:**
   - **Environment:** Should be "Docker"
   - **Dockerfile Path:** Should be `./Dockerfile`

2. **If not using Docker, switch to Docker:**
   - Go to Settings
   - Change Environment to "Docker"
   - Set Dockerfile Path: `./Dockerfile`
   - Save and redeploy

### Verify Cryptography Installation

Check Render build logs for:
```
Collecting cryptography>=41.0.0
Installing collected packages: cryptography
Successfully installed cryptography-...
```

If you don't see this, the build isn't picking up the new requirements.

---

## Quick Fix Checklist

- [ ] Code pushed to GitHub (cryptography in requirements.txt)
- [ ] Render service set to use Docker
- [ ] Clear build cache in Render
- [ ] Manual deploy latest commit
- [ ] Check build logs for cryptography installation
- [ ] Verify health endpoint works after deployment

---

## If All Else Fails

Temporarily disable encryption to get the service running:

1. Comment out encryption imports in code that uses it
2. Deploy to verify other parts work
3. Then fix cryptography installation
4. Re-enable encryption

But with the lazy imports, the service should start even if cryptography isn't available (encryption features just won't work).

