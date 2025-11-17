#!/bin/bash

# Setup Isolated Qdrant Instance for HygiaAI
# This script creates and runs a dedicated Qdrant instance on port 6334

echo "========================================"
echo "Setting up Isolated Qdrant for HygiaAI"
echo "========================================"
echo ""

# Check if Docker is running
echo "Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker."
    exit 1
fi
echo "✅ Docker is running"

# Stop and remove existing container if it exists
echo ""
echo "Checking for existing container..."
if docker ps -a --format '{{.Names}}' | grep -q "^hygiaai-qdrant$"; then
    echo "⚠️  Found existing container. Stopping and removing..."
    docker stop hygiaai-qdrant > /dev/null 2>&1
    docker rm hygiaai-qdrant > /dev/null 2>&1
    echo "✅ Removed existing container"
fi

# Create and start Qdrant container
echo ""
echo "Starting isolated Qdrant instance..."
echo "  Container name: hygiaai-qdrant"
echo "  Port mapping: 6334:6333 (external:internal)"
echo "  Data volume: hygiaai-qdrant-data"
echo ""

docker run -d \
    --name hygiaai-qdrant \
    -p 6334:6333 \
    -p 6335:6334 \
    -v hygiaai-qdrant-data:/qdrant/storage \
    qdrant/qdrant

if [ $? -eq 0 ]; then
    echo "✅ Qdrant container started successfully!"
    echo ""
    
    # Wait a moment for Qdrant to start
    echo "Waiting for Qdrant to initialize..."
    sleep 3
    
    # Check if Qdrant is responding
    echo ""
    echo "Verifying Qdrant is running..."
    if curl -s http://localhost:6334/health > /dev/null 2>&1; then
        echo "✅ Qdrant is healthy and responding!"
    else
        echo "⚠️  Qdrant is starting but not yet ready. It may take a few more seconds."
    fi
    
    echo ""
    echo "========================================"
    echo "Qdrant Instance Information"
    echo "========================================"
    echo "Container Name: hygiaai-qdrant"
    echo "API Endpoint: http://localhost:6334"
    echo "Dashboard: http://localhost:6334/dashboard"
    echo "Data Volume: hygiaai-qdrant-data"
    echo ""
    echo "To use this instance, set in your .env file:"
    echo "  QDRANT_HOST=localhost"
    echo "  QDRANT_PORT=6334"
    echo ""
    echo "Useful commands:"
    echo "  Stop: docker stop hygiaai-qdrant"
    echo "  Start: docker start hygiaai-qdrant"
    echo "  Logs: docker logs hygiaai-qdrant"
    echo "  Remove: docker rm -f hygiaai-qdrant"
    echo ""
else
    echo "❌ Failed to start Qdrant container"
    echo "Check Docker logs for errors"
    exit 1
fi

