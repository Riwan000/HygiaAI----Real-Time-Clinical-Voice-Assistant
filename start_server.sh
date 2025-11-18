#!/bin/bash
set -e

echo "Starting HygiaAI API Server..."
echo "Python version: $(python --version)"
echo "PORT: ${PORT:-8000}"

# Verify uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "ERROR: uvicorn not found in PATH"
    echo "PATH: $PATH"
    exit 1
fi

# Verify the app module can be imported
echo "Verifying app module can be imported..."
python -c "from src.api.main import app; print('App imported successfully')" || {
    echo "ERROR: Failed to import app module"
    exit 1
}

# Start the server
echo "Starting uvicorn server..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info

