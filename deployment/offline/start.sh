#!/bin/bash

# Start HygiaAI Offline Deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting HygiaAI services..."

# Check if .env.offline exists
if [ ! -f ".env.offline" ]; then
    echo "Error: .env.offline not found. Please copy .env.offline.example to .env.offline and configure it."
    exit 1
fi

# Start services with docker-compose
docker-compose up -d

echo "Waiting for services to be healthy..."
sleep 10

# Check service health
./health-check.sh

echo ""
echo "Services started successfully!"
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""

