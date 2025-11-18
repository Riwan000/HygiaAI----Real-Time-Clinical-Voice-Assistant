#!/bin/bash
# Script to run WebSocket proxy tests

set -e

echo "🧪 Running WebSocket Proxy Tests"
echo "=================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Run unit tests
echo ""
echo "📋 Running Unit Tests (Mocked)..."
pytest tests/test_websocket_proxy.py -v --tb=short

# Check if backend is running for integration tests
echo ""
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8000/api/v1/transcription/health > /dev/null 2>&1; then
    echo "✅ Backend is running. Running integration tests..."
    pytest tests/test_websocket_proxy_integration.py -v -m integration --tb=short
else
    echo "⚠️  Backend not running. Skipping integration tests."
    echo "   To run integration tests, start the backend server first:"
    echo "   uvicorn src.main:app --reload"
fi

echo ""
echo "✅ Test run complete!"

