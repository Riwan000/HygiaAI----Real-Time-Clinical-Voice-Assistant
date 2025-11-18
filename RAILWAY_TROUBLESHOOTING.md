# Railway Deployment Troubleshooting

## Healthcheck Failed - Service Unavailable

### Problem
Build succeeds but healthcheck fails with "service unavailable" errors.

### Common Causes & Solutions

#### 1. **Missing Environment Variables**

**Symptoms:** App crashes on startup, logs show connection errors

**Solution:** Add required environment variables in Railway:
```
DEEPGRAM_API_KEY=your_key (optional for basic health check)
QDRANT_HOST=your-cluster.qdrant.io (can use localhost for testing)
QDRANT_PORT=6333
QDRANT_API_KEY=your_key (optional if using local Qdrant)
PORT=8000 (Railway sets this automatically)
```

#### 2. **Router Import Failures**

**Symptoms:** App fails to start, import errors in logs

**Solution:** 
- Check Railway logs for specific import errors
- The updated `main.py` now handles import failures gracefully
- Ensure all dependencies are in `requirements.txt`

#### 3. **Port Binding Issues**

**Symptoms:** App starts but can't bind to port

**Solution:**
- **Always use `$PORT`** in start command, not hardcoded `8000`
- Start command should be: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

#### 4. **Missing Dependencies**

**Symptoms:** Import errors, module not found

**Solution:**
- Verify `python-dotenv` is in `requirements.txt` (now added)
- Check Railway build logs for missing packages
- Ensure all dependencies are listed in `requirements.txt`

#### 5. **Qdrant Connection Issues**

**Symptoms:** App hangs or crashes when trying to connect to Qdrant

**Solution:**
- For initial deployment, you can use a mock/test Qdrant
- Set `QDRANT_HOST=localhost` temporarily to test
- Or use Qdrant Cloud (recommended)

### Debugging Steps

1. **Check Railway Logs:**
   - Go to Railway dashboard → Your service → Logs
   - Look for error messages or stack traces
   - Check if app is starting or crashing

2. **Test Health Endpoint Manually:**
   - After deployment, try: `curl https://your-app.railway.app/health`
   - Should return: `{"status":"healthy","service":"HygiaAI API"}`

3. **Verify Start Command:**
   - Check Railway settings → Start Command
   - Should be: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - NOT: `python run_server.py` (that uses hardcoded port 8000)

4. **Check Environment Variables:**
   - Railway dashboard → Variables tab
   - Verify all required vars are set
   - Check for typos in variable names

5. **Test Locally First:**
   ```bash
   # Set environment variables
   export QDRANT_HOST=localhost
   export QDRANT_PORT=6334
   export PORT=8000
   
   # Run the same command Railway uses
   uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   
   # Test health endpoint
   curl http://localhost:8000/health
   ```

### Quick Fix Checklist

- [ ] Start command uses `$PORT` not `8000`
- [ ] Healthcheck path is `/health`
- [ ] All environment variables are set
- [ ] `python-dotenv` is in requirements.txt
- [ ] Check Railway logs for specific errors
- [ ] Test health endpoint manually after deployment

### Minimal Working Configuration

For a minimal deployment that just passes healthcheck:

**Start Command:**
```
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables (Minimum):**
```
PORT=8000
QDRANT_HOST=localhost
QDRANT_PORT=6334
```

**Healthcheck Path:**
```
/health
```

The `/health` endpoint doesn't require any external services, so it should work even if Qdrant isn't configured.

### Still Not Working?

1. **Check Railway Logs** - Most important step!
2. **Try removing healthcheck temporarily** - Deploy without healthcheck to see if app starts
3. **Simplify start command** - Use minimal uvicorn command
4. **Check Python version** - Railway uses Python 3.13, ensure compatibility
5. **Contact Railway support** - They can check server-side issues

### Updated Files

The following files have been updated to fix common issues:

1. **`src/api/main.py`** - Now handles router import failures gracefully
2. **`requirements.txt`** - Added `python-dotenv` dependency
3. **`railway.json`** - Added healthcheck path configuration

### Next Steps

After fixing the healthcheck:

1. Verify deployment is healthy
2. Test API endpoints: `https://your-app.railway.app/docs`
3. Configure Qdrant Cloud
4. Update frontend to use backend URL
5. Test end-to-end functionality

