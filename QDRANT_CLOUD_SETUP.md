# Qdrant Cloud Setup Guide

## Quick Setup

### Option 1: Manual Setup (Recommended)

Add these lines to your `.env` file:

```env
# Qdrant Cloud Configuration
QDRANT_URL=https://c92cec87-f4ea-4566-abd9-abc4fbc17f60.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.S6gttpfZ-qg4ElruY8_ci993FfLE6ujG3_ad4pc8fkg
```

**Replace with your actual values:**
- `QDRANT_URL`: Your Qdrant Cloud cluster URL
- `QDRANT_API_KEY`: Your Qdrant API key (JWT token)

### Option 2: Interactive Setup

Run the setup script:

```bash
python setup_qdrant_cloud.py
```

---

## Test Connection

After adding the configuration, test the connection:

```bash
python test_qdrant_connection.py
```

You should see:
```
✅ Success! Connected to Qdrant Cloud
   Found X collection(s):
     - collection_name_1
     - collection_name_2
```

---

## How It Works

The code automatically detects if `QDRANT_URL` is set:

- **If `QDRANT_URL` is set:** Uses cloud connection with URL + API key
- **If `QDRANT_URL` is not set:** Falls back to local connection with `QDRANT_HOST` and `QDRANT_PORT`

This means:
- ✅ Cloud setup: Just set `QDRANT_URL` and `QDRANT_API_KEY`
- ✅ Local setup: Set `QDRANT_HOST` and `QDRANT_PORT` (or use defaults)

---

## Environment Variables

### For Cloud (Qdrant Cloud):
```env
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key_here
```

### For Local (Docker):
```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
# QDRANT_API_KEY is optional for local
```

---

## Updated Code

The `QdrantStorage` class now supports both:

1. **Cloud connection** (using `url` parameter):
   ```python
   storage = QdrantStorage(
       url="https://xxx.cloud.qdrant.io:6333",
       api_key="your_api_key"
   )
   ```

2. **Local connection** (using `host`/`port`):
   ```python
   storage = QdrantStorage(
       host="localhost",
       port=6333
   )
   ```

---

## Verification

After setup, restart your server and check the logs:

```
INFO: Qdrant storage initialized (Cloud): https://xxx.cloud.qdrant.io:6333/hygiaai_cases
```

If you see "(Cloud)" in the log, you're using Qdrant Cloud! 🎉

---

## Troubleshooting

### Error: "QDRANT_URL not found"
- Make sure you've added `QDRANT_URL` to your `.env` file
- Restart your application after updating `.env`

### Error: "Authentication failed"
- Verify your `QDRANT_API_KEY` is correct
- Check that the API key hasn't expired
- Ensure the API key has the correct permissions

### Error: "Connection refused"
- Check that your Qdrant Cloud cluster is running
- Verify the URL is correct (including `https://` and port `:6333`)
- Check your network/firewall settings

---

**Done!** Your application will now use Qdrant Cloud instead of Docker.

