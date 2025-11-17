# Qdrant Setup Guide for HygiaAI

## Prerequisites

1. **Docker Desktop** must be installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Make sure Docker Desktop is started before running setup scripts

## Quick Start

### Windows (PowerShell)
```powershell
# Make sure Docker Desktop is running first!
.\examples\setup_isolated_qdrant.ps1
```

### Linux/Mac (Bash)
```bash
# Make sure Docker is running first!
chmod +x examples/setup_isolated_qdrant.sh
./examples/setup_isolated_qdrant.sh
```

### Manual Docker Command
```bash
docker run -d \
  --name hygiaai-qdrant \
  -p 6334:6333 \
  -p 6335:6334 \
  -v hygiaai-qdrant-data:/qdrant/storage \
  qdrant/qdrant
```

## Configuration

After starting Qdrant, update your `.env` file:

```bash
QDRANT_HOST=localhost
QDRANT_PORT=6334
```

## Verification

Check if Qdrant is running:
```bash
# Check container status
docker ps --filter "name=hygiaai-qdrant"

# Check health
curl http://localhost:6334/health

# Or use the isolation check script
python examples/check_qdrant_isolation.py
```

## Container Management

```bash
# Stop the container
docker stop hygiaai-qdrant

# Start the container
docker start hygiaai-qdrant

# View logs
docker logs hygiaai-qdrant

# Remove the container (data is preserved in volume)
docker rm -f hygiaai-qdrant

# Remove container and data volume
docker rm -f hygiaai-qdrant
docker volume rm hygiaai-qdrant-data
```

## Access Points

- **API Endpoint**: http://localhost:6334
- **Dashboard**: http://localhost:6334/dashboard
- **Health Check**: http://localhost:6334/health

## Troubleshooting

### Docker not running:
```
Error: Cannot connect to Docker daemon
```
**Solution**: Start Docker Desktop application

### Port already in use:
```
Error: Bind for 0.0.0.0:6334 failed: port is already allocated
```
**Solution**: 
- Check what's using port 6334: `netstat -ano | findstr :6334` (Windows) or `lsof -i :6334` (Linux/Mac)
- Stop the conflicting service or use a different port

### Container name already exists:
```
Error: Conflict. The container name "hygiaai-qdrant" is already in use
```
**Solution**: 
```bash
docker rm -f hygiaai-qdrant
# Then run setup script again
```

## Data Persistence

Data is stored in a Docker volume named `hygiaai-qdrant-data`. This means:
- Data persists even if container is removed
- Data is isolated from other Qdrant instances
- To completely remove data: `docker volume rm hygiaai-qdrant-data`

## Isolation Benefits

✅ **Port Isolation**: Uses port 6334 instead of default 6333
✅ **Container Isolation**: Named container `hygiaai-qdrant`
✅ **Data Isolation**: Separate Docker volume
✅ **Collection Isolation**: All collections use `hygiaai_` prefix

This ensures no conflicts with other projects using Qdrant.

