#!/bin/bash
# HygiaAI Offline Demo Startup Script
# Starts all required services for offline demonstration

set -e

echo "=================================================================================="
echo "  HygiaAI Offline Demo Startup"
echo "=================================================================================="
echo ""

# Check if Docker is running
echo "Checking Docker..."
if docker ps > /dev/null 2>&1; then
    echo "✓ Docker is running"
else
    echo "✗ Docker is not running. Please start Docker."
    exit 1
fi

# Start Qdrant
echo ""
echo "Starting Qdrant vector database..."
if docker ps --filter "name=hygiaai-qdrant" --format "{{.Names}}" | grep -q "hygiaai-qdrant"; then
    echo "✓ Qdrant is already running"
else
    if docker ps -a --filter "name=hygiaai-qdrant" --format "{{.Names}}" | grep -q "hygiaai-qdrant"; then
        docker start hygiaai-qdrant > /dev/null
        echo "✓ Qdrant container started"
    else
        echo "Creating Qdrant container..."
        docker run -d \
            -p 6334:6333 \
            -p 6335:6334 \
            --name hygiaai-qdrant \
            -v hygiaai-qdrant-data:/qdrant/storage \
            qdrant/qdrant > /dev/null
        echo "✓ Qdrant container created and started"
    fi
fi

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
max_attempts=30
attempt=0
qdrant_ready=false

while [ $attempt -lt $max_attempts ] && [ "$qdrant_ready" = false ]; do
    if curl -s http://localhost:6334/health > /dev/null 2>&1; then
        qdrant_ready=true
        echo "✓ Qdrant is ready"
    else
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    fi
done

if [ "$qdrant_ready" = false ]; then
    echo ""
    echo "⚠ Qdrant may not be ready yet, but continuing..."
fi

# Check if backend is already running
echo ""
echo "Checking backend server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is already running"
else
    echo "Starting backend server..."
    echo "  (Backend will run in background)"
    
    # Start backend in background
    python run_server.py > /dev/null 2>&1 &
    BACKEND_PID=$!
    echo "✓ Backend server starting... (PID: $BACKEND_PID)"
    sleep 3
fi

# Check if frontend is already running
echo ""
echo "Checking frontend server..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend is already running"
else
    echo "Starting frontend server..."
    echo "  (Frontend will run in background)"
    
    # Start frontend in background
    cd frontend
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo "✓ Frontend server starting... (PID: $FRONTEND_PID)"
    sleep 5
fi

# Summary
echo ""
echo "=================================================================================="
echo "  Demo Ready!"
echo "=================================================================================="
echo ""
echo "Services:"
echo "  • Qdrant:     http://localhost:6334"
echo "  • Backend:    http://localhost:8000"
echo "  • Frontend:   http://localhost:3000"
echo ""
echo "Open your browser to: http://localhost:3000"
echo ""

# Try to open browser (platform-specific)
if command -v xdg-open > /dev/null; then
    # Linux
    xdg-open http://localhost:3000 > /dev/null 2>&1 &
elif command -v open > /dev/null; then
    # macOS
    open http://localhost:3000 > /dev/null 2>&1 &
fi

echo "Demo is running!"
echo ""
echo "To stop all services, press Ctrl+C or run: ./scripts/stop_offline_demo.sh"
echo ""

# Keep script running
wait

