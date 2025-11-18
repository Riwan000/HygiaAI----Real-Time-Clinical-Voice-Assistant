#!/bin/bash

# Health Check Script for HygiaAI Offline Deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Checking service health..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Qdrant
echo -n "Qdrant: "
if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check Backend API
echo -n "Backend API: "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s -f http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${YELLOW}⚠ Not responding (may be starting)${NC}"
fi

# Check Docker containers
echo ""
echo "Docker container status:"
docker-compose ps

echo ""
echo "For detailed logs, run: docker-compose logs"

