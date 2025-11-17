# How to Check Qdrant Isolated Instance

This guide shows you multiple ways to verify and check your isolated Qdrant instance.

## Quick Check Methods

### 1. Run the Comprehensive Test Suite (Recommended)

```bash
python examples/test_qdrant_isolated_instance.py
```

This runs all 7 tests:
- Connection verification
- Collection verification
- Data storage/retrieval
- Similarity search
- Filtering
- Multi-collection support
- Collection info

### 2. Run the Isolation Check

```bash
python examples/check_qdrant_isolation.py
```

This verifies:
- Qdrant is accessible
- All collections exist
- No conflicts with other projects
- Configuration is correct

### 3. Check Collections Status

```bash
python examples/initialize_qdrant_collections.py
```

This shows:
- Which collections exist
- Their vector sizes
- Verification status

## Web Dashboard

### Access Qdrant Dashboard

Open in your browser:
```
http://localhost:6334/dashboard
```

The dashboard shows:
- All collections
- Points count
- Vector dimensions
- Search interface
- Collection statistics

### Health Check

```
http://localhost:6334/health
```

Should return: `{"status":"ok"}`

## Command Line Checks

### 1. Check Docker Container Status

```powershell
# Windows PowerShell
docker ps --filter "name=hygiaai-qdrant"

# Should show:
# CONTAINER ID   IMAGE            STATUS         PORTS                    NAMES
# xxxxx          qdrant/qdrant    Up X minutes   0.0.0.0:6334->6333/tcp  hygiaai-qdrant
```

### 2. Check Container Logs

```powershell
docker logs hygiaai-qdrant
```

### 3. Check if Port is Listening

```powershell
# Windows
netstat -ano | findstr :6334

# Should show:
# TCP    0.0.0.0:6334    0.0.0.0:0    LISTENING
```

## Python Scripts

### Quick Connection Test

Create a file `quick_check.py`:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6334)
collections = client.get_collections()
print(f"✅ Connected! Found {len(collections.collections)} collections")
for col in collections.collections:
    print(f"  - {col.name}")
```

Run: `python quick_check.py`

### Check Collection Details

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6334)
collection_name = "hygiaai_transcripts"
info = client.get_collection(collection_name)
print(f"Collection: {collection_name}")
print(f"Points: {info.points_count}")
print(f"Vector Size: {info.config.params.vectors.size}")
```

## Using QdrantStorage Class

### Test Storage Operations

```python
from src.storage.qdrant_storage import QdrantStorage

# Initialize
storage = QdrantStorage(
    host="localhost",
    port=6334,
    collection_name="hygiaai_transcripts"
)

# Get collection info
info = storage.get_collection_info()
print(f"Collection: {info['name']}")
print(f"Vector Size: {info['vector_size']}")
print(f"Points: {info.get('points_count', 0)}")
```

## API Endpoints

### List Collections

```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:6334/collections" | Select-Object -ExpandProperty Content

# Or with curl (if available)
curl http://localhost:6334/collections
```

### Get Collection Info

```powershell
Invoke-WebRequest -Uri "http://localhost:6334/collections/hygiaai_transcripts" | Select-Object -ExpandProperty Content
```

### Health Check

```powershell
Invoke-WebRequest -Uri "http://localhost:6334/health" | Select-Object -ExpandProperty Content
```

## Verification Checklist

Use this checklist to verify everything is working:

- [ ] Docker container is running
- [ ] Port 6334 is accessible
- [ ] Health endpoint returns OK
- [ ] Dashboard is accessible
- [ ] All 3 collections exist:
  - [ ] `hygiaai_transcripts`
  - [ ] `hygiaai_knowledge_base`
  - [ ] `hygiaai_cases`
- [ ] Collections have correct vector size (768)
- [ ] Can store data
- [ ] Can retrieve data
- [ ] Similarity search works
- [ ] No other projects' collections found

## Troubleshooting

### Container Not Running

```powershell
# Start the container
docker start hygiaai-qdrant

# Or recreate it
.\examples\setup_isolated_qdrant.ps1
```

### Port Not Accessible

```powershell
# Check if port is in use
netstat -ano | findstr :6334

# Check Docker port mapping
docker port hygiaai-qdrant
```

### Connection Refused

1. Check Docker Desktop is running
2. Check container is running: `docker ps`
3. Check port mapping: `docker port hygiaai-qdrant`
4. Try restarting: `docker restart hygiaai-qdrant`

## Quick Reference

| Method | Command | What It Checks |
|--------|---------|----------------|
| Full Test | `python examples/test_qdrant_isolated_instance.py` | All functionality |
| Isolation | `python examples/check_qdrant_isolation.py` | Isolation & config |
| Collections | `python examples/initialize_qdrant_collections.py` | Collection status |
| Dashboard | `http://localhost:6334/dashboard` | Web UI |
| Health | `http://localhost:6334/health` | Server status |
| Docker | `docker ps --filter "name=hygiaai-qdrant"` | Container status |

## Next Steps

After verifying everything works:
1. Set environment variables in `.env`:
   ```
   QDRANT_HOST=localhost
   QDRANT_PORT=6334
   ```
2. Start using QdrantStorage in your code
3. Store your first transcript/case
4. Test similarity search with real data

