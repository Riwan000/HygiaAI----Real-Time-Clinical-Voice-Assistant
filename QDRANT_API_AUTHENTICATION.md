# Qdrant API Authentication Guide

Complete guide to setting up and using Qdrant API keys for secure cloud deployments.

---

## 🔐 Why Use API Keys?

- **Security:** Protect your Qdrant instance from unauthorized access
- **Required for Qdrant Cloud:** All Qdrant Cloud instances require API keys
- **Production Best Practice:** Essential for production deployments
- **Access Control:** Control who can access your vector database

---

## 🎯 Option 1: Qdrant Cloud (API Key Required)

### Setup:

1. **Sign up at [Qdrant Cloud](https://cloud.qdrant.io)**
2. **Create a cluster**
3. **Get your API key:**
   - Go to cluster dashboard
   - Navigate to "API Keys" section
   - Copy your API key (starts with `qdrant_`)

### Configuration:

**In Railway (Backend Service) → Variables:**
```
QDRANT_HOST=your-cluster-name.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=qdrant_your_api_key_here
```

**Note:** Qdrant Cloud uses HTTPS, so the port might be `443` or `6333` depending on your setup.

---

## 🚂 Option 2: Railway Self-Hosted (Optional API Key)

### Enable API Key Authentication:

1. **In Railway Qdrant Service → Variables:**
   ```
   QDRANT_API_KEY=your_secret_key_here
   ```

2. **Qdrant will automatically use this environment variable**

3. **Update Backend Variables:**
   ```
   QDRANT_HOST=your-qdrant.railway.app
   QDRANT_PORT=6333
   QDRANT_API_KEY=your_secret_key_here
   ```

**Note:** Railway self-hosted Qdrant doesn't require API keys by default, but it's recommended for security.

---

## 🔧 Option 3: Self-Hosted with API Key

### Using Docker:

**docker-compose.yml:**
```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT_API_KEY=your_secret_key_here
    ports:
      - "6333:6333"
```

### Using Command Line:

```bash
docker run -d \
  -p 6333:6333 \
  -e QDRANT_API_KEY=your_secret_key_here \
  qdrant/qdrant:latest
```

---

## 💻 Code Implementation

### Updated QdrantStorage Class

The `QdrantStorage` class now supports API keys:

```python
from src.storage.qdrant_storage import QdrantStorage

# With API key
storage = QdrantStorage(
    host="your-cluster.qdrant.io",
    port=6333,
    api_key="qdrant_your_api_key_here",
    collection_name="hygiaai_cases"
)

# Without API key (local development)
storage = QdrantStorage(
    host="localhost",
    port=6333,
    collection_name="hygiaai_cases"
)
```

### Environment Variable Usage

The code automatically reads from environment variables:

```python
# Automatically uses QDRANT_API_KEY from environment
storage = QdrantStorage(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
    # api_key is automatically read from QDRANT_API_KEY env var
    collection_name="hygiaai_cases"
)
```

---

## 🔑 Generating Secure API Keys

### For Qdrant Cloud:
- API keys are automatically generated
- Format: `qdrant_xxxxxxxxxxxxx`
- Copy from dashboard

### For Self-Hosted:
Generate a secure random key:

**Python:**
```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)
```

**Bash:**
```bash
openssl rand -base64 32
```

**Node.js:**
```javascript
require('crypto').randomBytes(32).toString('base64')
```

---

## 📋 Environment Variables Reference

### Required for Qdrant Cloud:
```
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=qdrant_your_api_key_here
```

### Optional for Self-Hosted:
```
QDRANT_HOST=localhost (or your-host.com)
QDRANT_PORT=6333
QDRANT_API_KEY=your_secret_key (optional but recommended)
```

---

## 🧪 Testing API Key Authentication

### Test Connection:

```python
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    host=os.getenv("QDRANT_HOST"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Test connection
collections = client.get_collections()
print(f"Connected! Collections: {collections}")
```

### Test with cURL:

**Without API Key (local):**
```bash
curl http://localhost:6333/health
```

**With API Key (Qdrant Cloud):**
```bash
curl -H "api-key: qdrant_your_api_key" \
     https://your-cluster.qdrant.io:6333/health
```

---

## 🔒 Security Best Practices

### 1. **Never Commit API Keys**
- Add to `.gitignore`: `.env`
- Use environment variables only
- Never hardcode in source code

### 2. **Use Different Keys for Different Environments**
- Development: `QDRANT_API_KEY_DEV`
- Production: `QDRANT_API_KEY_PROD`
- Staging: `QDRANT_API_KEY_STAGING`

### 3. **Rotate Keys Regularly**
- Change API keys every 90 days
- Update in all environments simultaneously
- Revoke old keys immediately

### 4. **Restrict Access**
- Use IP whitelisting if available
- Use VPN for production access
- Monitor API key usage

### 5. **Use HTTPS**
- Qdrant Cloud uses HTTPS automatically
- Self-hosted: Use reverse proxy (nginx) with SSL

---

## 🚨 Troubleshooting

### Error: "Unauthorized" or "401"

**Cause:** Invalid or missing API key

**Solution:**
1. Verify API key is correct
2. Check environment variable is set
3. Ensure API key has correct format (for Qdrant Cloud: starts with `qdrant_`)

### Error: "Connection Refused"

**Cause:** Wrong host/port or API key not configured

**Solution:**
1. Verify `QDRANT_HOST` and `QDRANT_PORT`
2. Check if Qdrant is running
3. Test without API key first (if self-hosted)

### Error: "Forbidden" or "403"

**Cause:** API key doesn't have required permissions

**Solution:**
1. Check API key permissions in Qdrant Cloud dashboard
2. Regenerate API key if needed
3. Verify key is for correct cluster

---

## 📊 API Key Formats

### Qdrant Cloud:
```
Format: qdrant_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Example: qdrant_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

### Self-Hosted:
```
Format: Any secure random string
Example: aB3dEf9gHiJkLmNoPqRsTuVwXyZ1234567890
```

---

## 🔄 Migration Guide

### From Local (No Auth) to Cloud (With Auth):

1. **Get Qdrant Cloud API key**
2. **Update environment variables:**
   ```
   QDRANT_HOST=your-cluster.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=qdrant_your_key
   ```
3. **Test connection**
4. **Re-populate data:**
   ```bash
   python scripts/populate_extended_demo_data.py
   ```

### From Self-Hosted (No Auth) to Self-Hosted (With Auth):

1. **Generate API key**
2. **Restart Qdrant with API key:**
   ```bash
   docker run -e QDRANT_API_KEY=your_key qdrant/qdrant
   ```
3. **Update backend environment variables**
4. **Restart backend**

---

## ✅ Checklist

- [ ] API key generated/obtained
- [ ] Environment variables set in Railway
- [ ] Code updated to use API keys
- [ ] Connection tested
- [ ] API key stored securely (not in code)
- [ ] Different keys for dev/prod
- [ ] Documentation updated

---

## 🎯 Quick Reference

### Railway Configuration:

**Backend Service Variables:**
```
QDRANT_HOST=your-qdrant.railway.app
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key_here
```

### Code Usage:

```python
# Automatic (reads from env vars)
storage = QdrantStorage(
    host=os.getenv("QDRANT_HOST"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
    # api_key automatically read from QDRANT_API_KEY
)
```

---

## 📚 Additional Resources

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [Qdrant Authentication Guide](https://qdrant.tech/documentation/guides/authentication/)
- [Qdrant Python Client](https://qdrant.github.io/qdrant-client/)

---

**Updated:** Code now supports API keys automatically via `QDRANT_API_KEY` environment variable.

