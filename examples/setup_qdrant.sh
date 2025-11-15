#!/bin/bash
# Quick setup script for Qdrant

echo "Setting up Qdrant for HygiaAI..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Qdrant is already running
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "✓ Qdrant is already running on localhost:6333"
    exit 0
fi

# Start Qdrant
echo "Starting Qdrant container..."
docker run -d \
    --name qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
sleep 5

# Check health
if curl -s http://localhost:6333/health | grep -q "ok"; then
    echo "✓ Qdrant is running successfully!"
    echo "  Health check: http://localhost:6333/health"
    echo "  Dashboard: http://localhost:6333/dashboard"
else
    echo "⚠ Qdrant may not be ready yet. Check with: curl http://localhost:6333/health"
fi

echo ""
echo "To stop Qdrant: docker stop qdrant"
echo "To remove Qdrant: docker rm qdrant"

