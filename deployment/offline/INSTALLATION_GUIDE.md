# HygiaAI Offline Rural Deployment Kit - Installation Guide

This guide provides step-by-step instructions for deploying HygiaAI in offline rural environments where internet connectivity is limited or unavailable.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Starting Services](#starting-services)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Overview

The HygiaAI Offline Deployment Kit enables full functionality of the clinical voice assistant without requiring constant internet connectivity. The kit includes:

- **Qdrant Vector Database**: Local vector storage for clinical cases and knowledge base
- **Backend API**: FastAPI server with all core functionality
- **Frontend**: React-based web interface
- **Docker Compose**: Orchestration for all services

### Key Features

- ✅ Fully offline operation (no external API dependencies)
- ✅ Local vector database (Qdrant)
- ✅ Pre-configured Docker containers
- ✅ Easy installation scripts
- ✅ Health monitoring
- ✅ Data persistence

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+) or Windows 10/11
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ free space (for data and Docker images)
- **Docker**: Version 20.10+ with Docker Compose plugin

### Software Requirements

1. **Docker Engine** (required)
   - Linux: Install via package manager or Docker's official script
   - Windows: Docker Desktop for Windows

2. **Docker Compose** (required)
   - Usually included with Docker Desktop
   - Linux: Install separately if needed

3. **Internet Connection** (only for initial setup)
   - Required only for downloading Docker images
   - Can use pre-downloaded images for fully offline installation

## Installation

### Linux Installation

1. **Download the deployment kit** to your server:
   ```bash
   # If you have the repository
   cd /path/to/HygiaAI----Real-Time-Clinical-Voice-Assistant
   
   # Or extract from a deployment package
   tar -xzf hygiaai-offline-kit.tar.gz
   cd hygiaai-offline-kit
   ```

2. **Make installation script executable**:
   ```bash
   chmod +x deployment/offline/install.sh
   ```

3. **Run the installation script**:
   ```bash
   sudo ./deployment/offline/install.sh [INSTALL_DIR]
   ```
   
   Default installation directory: `/opt/hygiaai`
   Custom directory: `sudo ./deployment/offline/install.sh /custom/path`

4. **Follow the prompts** and wait for installation to complete.

### Windows Installation

1. **Open PowerShell as Administrator**:
   - Right-click PowerShell → "Run as Administrator"

2. **Navigate to the deployment kit directory**:
   ```powershell
   cd C:\path\to\HygiaAI----Real-Time-Clinical-Voice-Assistant
   ```

3. **Run the installation script**:
   ```powershell
   .\deployment\offline\install.ps1 [INSTALL_DIR]
   ```
   
   Default installation directory: `C:\HygiaAI`
   Custom directory: `.\deployment\offline\install.ps1 D:\HygiaAI`

4. **Follow the prompts** and wait for installation to complete.

### Fully Offline Installation

If you don't have internet access during installation:

1. **Pre-download Docker images** on a machine with internet:
   ```bash
   docker pull qdrant/qdrant:latest
   docker pull python:3.11-slim
   docker pull node:20-alpine
   docker pull nginx:alpine
   ```

2. **Save images to a file**:
   ```bash
   docker save qdrant/qdrant:latest python:3.11-slim node:20-alpine nginx:alpine -o hygiaai-images.tar
   ```

3. **Transfer the images file** to the offline server

4. **Load images on the offline server**:
   ```bash
   docker load -i hygiaai-images.tar
   ```

5. **Proceed with normal installation** (it will use the pre-loaded images)

## Configuration

### Environment Configuration

1. **Navigate to installation directory**:
   ```bash
   cd /opt/hygiaai  # Linux
   # or
   cd C:\HygiaAI  # Windows
   ```

2. **Copy environment template**:
   ```bash
   # Linux
   cp env.offline.example .env.offline
   
   # Windows
   copy env.offline.example .env.offline
   ```

3. **Edit `.env.offline`** with your settings:
   ```bash
   # Linux
   nano .env.offline
   
   # Windows
   notepad .env.offline
   ```

### Key Configuration Options

- **QDRANT_HOST**: Qdrant service name (default: `qdrant`)
- **QDRANT_PORT**: Qdrant port (default: `6333`)
- **API_PORT**: Backend API port (default: `8000`)
- **ENCRYPTION_KEY**: **IMPORTANT**: Change this to a secure random key
- **LOG_LEVEL**: Logging verbosity (INFO, DEBUG, WARNING, ERROR)

### Generate Encryption Key

For production deployments, generate a secure encryption key:

```bash
# Linux
openssl rand -hex 32

# Windows PowerShell
-join ((1..32) | ForEach-Object {'{0:X}' -f (Get-Random -Maximum 256)})
```

Update `ENCRYPTION_KEY` in `.env.offline` with the generated key.

## Starting Services

### Linux

```bash
cd /opt/hygiaai
./start.sh
```

### Windows

```powershell
cd C:\HygiaAI
.\start.ps1
```

### Manual Start

If you prefer to start manually:

```bash
docker-compose up -d
```

This starts all services in detached mode (background).

## Verification

### Health Check

Run the health check script:

```bash
# Linux
./health-check.sh

# Windows
.\health-check.ps1
```

### Manual Verification

1. **Check Qdrant**:
   ```bash
   curl http://localhost:6333/health
   ```

2. **Check Backend API**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Frontend**:
   Open browser: `http://localhost:3000`

4. **Check API Documentation**:
   Open browser: `http://localhost:8000/docs`

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs qdrant

# Follow logs (real-time)
docker-compose logs -f
```

## Troubleshooting

### Services Won't Start

1. **Check Docker status**:
   ```bash
   docker ps
   docker-compose ps
   ```

2. **Check port availability**:
   ```bash
   # Linux
   netstat -tuln | grep -E '3000|8000|6333'
   
   # Windows
   netstat -an | findstr "3000 8000 6333"
   ```

3. **Check logs**:
   ```bash
   docker-compose logs
   ```

### Port Conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change external port
```

### Out of Disk Space

1. **Clean up Docker**:
   ```bash
   docker system prune -a
   ```

2. **Check disk usage**:
   ```bash
   # Linux
   df -h
   du -sh /var/lib/docker
   
   # Windows
   Get-PSDrive C
   ```

### Qdrant Connection Issues

1. **Verify Qdrant is running**:
   ```bash
   docker-compose ps qdrant
   ```

2. **Check Qdrant logs**:
   ```bash
   docker-compose logs qdrant
   ```

3. **Restart Qdrant**:
   ```bash
   docker-compose restart qdrant
   ```

### Backend API Issues

1. **Check backend logs**:
   ```bash
   docker-compose logs backend
   ```

2. **Verify environment variables**:
   ```bash
   docker-compose exec backend env | grep QDRANT
   ```

3. **Restart backend**:
   ```bash
   docker-compose restart backend
   ```

## Maintenance

### Stopping Services

```bash
# Linux
./stop.sh

# Windows
.\stop.ps1

# Or manually
docker-compose down
```

### Updating Services

1. **Pull latest images** (if internet available):
   ```bash
   docker-compose pull
   ```

2. **Rebuild containers**:
   ```bash
   docker-compose up -d --build
   ```

### Backup Data

1. **Backup Qdrant data**:
   ```bash
   docker run --rm -v hygiaai-qdrant-data:/data -v $(pwd):/backup \
     alpine tar czf /backup/qdrant-backup.tar.gz -C /data .
   ```

2. **Backup application data**:
   ```bash
   tar czf data-backup.tar.gz data/ logs/
   ```

### Restore Data

1. **Restore Qdrant**:
   ```bash
   docker run --rm -v hygiaai-qdrant-data:/data -v $(pwd):/backup \
     alpine tar xzf /backup/qdrant-backup.tar.gz -C /data
   ```

2. **Restart services**:
   ```bash
   docker-compose restart
   ```

### Monitoring

Monitor resource usage:

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Support

For issues or questions:

1. Check logs: `docker-compose logs`
2. Review this guide's troubleshooting section
3. Check the main project documentation
4. Review GitHub issues (if internet available)

## Security Notes

- **Change default encryption key** in production
- **Use firewall rules** to restrict access
- **Enable HTTPS** for production deployments (requires additional configuration)
- **Regular backups** of data volumes
- **Keep Docker images updated** when possible

## Next Steps

After successful installation:

1. Configure sync layer (Task 77) for data synchronization when connectivity is available
2. Set up local model inference (Ollama) for fully offline LLM capabilities
3. Configure backup procedures
4. Set up monitoring and alerting

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-XX

