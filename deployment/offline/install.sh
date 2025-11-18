#!/bin/bash

# HygiaAI Offline Rural Deployment Kit - Linux Installation Script
# This script sets up HygiaAI for offline deployment in rural environments

set -e

echo "=========================================="
echo "HygiaAI Offline Deployment Kit"
echo "Linux Installation Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Warning: Not running as root. Some operations may require sudo.${NC}"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
MISSING_DEPS=()

if ! command_exists docker; then
    MISSING_DEPS+=("docker")
fi

if ! command_exists docker-compose; then
    MISSING_DEPS+=("docker-compose")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required dependencies: ${MISSING_DEPS[*]}${NC}"
    echo ""
    echo "Please install Docker and Docker Compose:"
    echo "  Ubuntu/Debian:"
    echo "    curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "    sh get-docker.sh"
    echo "    sudo apt-get install docker-compose-plugin"
    echo ""
    echo "  CentOS/RHEL:"
    echo "    curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "    sh get-docker.sh"
    echo "    sudo yum install docker-compose-plugin"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Get installation directory
INSTALL_DIR="${1:-/opt/hygiaai}"
echo "Installation directory: $INSTALL_DIR"

# Create installation directory
echo "Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R $USER:$USER "$INSTALL_DIR"

# Copy deployment files
echo "Copying deployment files..."
cp -r deployment/offline/* "$INSTALL_DIR/"
cp docker-compose.yml "$INSTALL_DIR/" 2>/dev/null || true

# Create necessary directories
echo "Creating data directories..."
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/config"

# Set up environment file
if [ ! -f "$INSTALL_DIR/.env.offline" ]; then
    echo "Creating environment configuration..."
    if [ -f "$INSTALL_DIR/env.offline.example" ]; then
        cp "$INSTALL_DIR/env.offline.example" "$INSTALL_DIR/.env.offline"
    elif [ -f "$INSTALL_DIR/.env.offline.example" ]; then
        cp "$INSTALL_DIR/.env.offline.example" "$INSTALL_DIR/.env.offline"
    fi
    echo -e "${YELLOW}Please edit $INSTALL_DIR/.env.offline with your configuration${NC}"
fi

# Set permissions
echo "Setting permissions..."
chmod +x "$INSTALL_DIR/install.sh"
chmod +x "$INSTALL_DIR/start.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/stop.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/health-check.sh" 2>/dev/null || true

# Pull Docker images (if internet available)
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "Pulling Docker images..."
    cd "$INSTALL_DIR"
    docker-compose pull || echo -e "${YELLOW}Warning: Could not pull images. Using local images if available.${NC}"
else
    echo -e "${YELLOW}No internet connection detected. Using local Docker images.${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Installation completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit configuration: $INSTALL_DIR/.env.offline"
echo "2. Start services: cd $INSTALL_DIR && ./start.sh"
echo "3. Check health: cd $INSTALL_DIR && ./health-check.sh"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""

