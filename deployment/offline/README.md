# HygiaAI Offline Rural Deployment Kit

This directory contains all files necessary for deploying HygiaAI in offline rural environments.

## Quick Start

### Linux
```bash
chmod +x install.sh
sudo ./install.sh
cd /opt/hygiaai
cp env.offline.example .env.offline
# Edit .env.offline with your configuration
./start.sh
```

### Windows
```powershell
.\install.ps1
cd C:\HygiaAI
copy env.offline.example .env.offline
# Edit .env.offline with your configuration
.\start.ps1
```

## Files

- **docker-compose.yml** - Docker Compose configuration for all services
- **Dockerfile.backend** - Backend API container definition
- **Dockerfile.frontend** - Frontend container definition
- **nginx.conf** - Nginx configuration for frontend
- **install.sh** / **install.ps1** - Installation scripts
- **start.sh** / **start.ps1** - Start services scripts
- **stop.sh** / **stop.ps1** - Stop services scripts
- **health-check.sh** / **health-check.ps1** - Health check scripts
- **env.offline.example** - Environment configuration template
- **INSTALLATION_GUIDE.md** - Comprehensive installation and usage guide

## Services

The deployment includes:

1. **Qdrant** - Vector database (port 6333)
2. **Backend API** - FastAPI server (port 8000)
3. **Frontend** - React web interface (port 3000)

## Documentation

See [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) for detailed instructions.

## Support

For issues or questions, refer to the main project documentation or check the troubleshooting section in the installation guide.

