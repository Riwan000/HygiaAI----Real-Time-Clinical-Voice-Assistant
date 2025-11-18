# Offline Deployment Checklist

Use this checklist to ensure a successful offline deployment of HygiaAI.

## Pre-Installation

- [ ] System meets minimum requirements (4+ CPU cores, 8GB+ RAM, 50GB+ storage)
- [ ] Docker Engine installed and running
- [ ] Docker Compose plugin installed
- [ ] Ports 3000, 8000, 6333 available (or configured differently)
- [ ] Sufficient disk space available
- [ ] (Optional) Docker images pre-downloaded for fully offline installation

## Installation

- [ ] Installation script executed successfully
- [ ] All files copied to installation directory
- [ ] Data directories created (data/, logs/, config/)
- [ ] Environment file created (.env.offline)

## Configuration

- [ ] `.env.offline` file edited with appropriate values
- [ ] Encryption key changed from default (if in production)
- [ ] Qdrant host/port configured correctly
- [ ] API port configured correctly
- [ ] Log level set appropriately
- [ ] Feature flags configured as needed

## Starting Services

- [ ] Services started successfully (`start.sh` or `start.ps1`)
- [ ] All containers running (`docker-compose ps`)
- [ ] No error messages in logs (`docker-compose logs`)

## Verification

- [ ] Health check script passes (`health-check.sh` or `health-check.ps1`)
- [ ] Qdrant accessible at http://localhost:6333/health
- [ ] Backend API accessible at http://localhost:8000/health
- [ ] Frontend accessible at http://localhost:3000
- [ ] API documentation accessible at http://localhost:8000/docs
- [ ] Qdrant dashboard accessible at http://localhost:6333/dashboard

## Post-Installation

- [ ] Test transcription functionality (if enabled)
- [ ] Test entity extraction (if enabled)
- [ ] Test RAG functionality (if enabled)
- [ ] Test visualization features (if enabled)
- [ ] Verify data persistence (restart services, check data)
- [ ] Set up backup procedures
- [ ] Configure monitoring (if needed)
- [ ] Document any custom configurations

## Security

- [ ] Encryption key changed from default
- [ ] Firewall rules configured (if applicable)
- [ ] Access controls set up (if applicable)
- [ ] Audit logging enabled (if needed)
- [ ] Regular backup schedule established

## Troubleshooting

If any step fails:

1. Check logs: `docker-compose logs [service-name]`
2. Verify configuration: Review `.env.offline`
3. Check system resources: `docker stats`
4. Review installation guide troubleshooting section
5. Check Docker daemon: `docker ps`

## Notes

Document any custom configurations or deviations from standard installation:

```
[Add notes here]
```

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Installation Directory**: _______________  
**Version**: 1.0.0

