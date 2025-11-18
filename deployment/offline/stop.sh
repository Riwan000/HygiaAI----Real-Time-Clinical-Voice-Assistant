#!/bin/bash

# Stop HygiaAI Offline Deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Stopping HygiaAI services..."

docker-compose down

echo "Services stopped."

