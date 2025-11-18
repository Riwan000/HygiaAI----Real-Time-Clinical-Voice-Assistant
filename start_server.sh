#!/bin/bash
set -e

# Output to both stdout and stderr for Railway logs
exec 1> >(tee /proc/self/fd/1 /proc/self/fd/2)

echo "=== Starting HygiaAI API Server ===" >&2
echo "Python version: $(python --version)" >&2
echo "PORT: ${PORT:-8000}" >&2
echo "PATH: $PATH" >&2

# Verify uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "ERROR: uvicorn not found in PATH" >&2
    echo "PATH: $PATH" >&2
    which python >&2
    python -m pip list | grep uvicorn >&2 || echo "uvicorn not in pip list" >&2
    exit 1
fi

echo "uvicorn found: $(which uvicorn)" >&2

# Verify the app module can be imported
echo "Verifying app module can be imported..." >&2
python -c "from src.api.main import app; print('App imported successfully')" 2>&1 || {
    echo "ERROR: Failed to import app module" >&2
    python -c "import sys; sys.path.insert(0, '.'); from src.api.main import app" 2>&1 || {
        echo "ERROR: Import failed even with path adjustment" >&2
        exit 1
    }
}

# Start the server
echo "Starting uvicorn server on port ${PORT:-8000}..." >&2
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info

