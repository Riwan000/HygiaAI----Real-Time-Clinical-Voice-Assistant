#!/bin/bash
# Stop HygiaAI Offline Demo Services

echo "Stopping HygiaAI demo services..."

# Stop frontend (find and kill npm dev server)
echo "Stopping frontend..."
pkill -f "npm run dev" || true
pkill -f "vite" || true

# Stop backend (find and kill Python server)
echo "Stopping backend..."
pkill -f "run_server.py" || true
pkill -f "uvicorn" || true

# Stop Qdrant
echo "Stopping Qdrant..."
docker stop hygiaai-qdrant > /dev/null 2>&1 || true

echo "✓ All services stopped"

