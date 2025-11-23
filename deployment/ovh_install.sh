#!/bin/bash
# OVH Installation Script for AI Invoice Insights
# This script sets up the application on an OVH server

set -e

echo "=== AI Invoice Insights - OVH Installation ==="
echo ""

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11+
echo "Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create application directory
echo "Setting up application directory..."
APP_DIR="/opt/ai-invoice-insights"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone repository (if not already present)
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/jerome79/ai-invoice-insights.git $APP_DIR
else
    echo "Updating existing repository..."
    cd $APP_DIR
    git pull
fi

cd $APP_DIR

# Build and start services
echo "Building and starting Docker containers..."
docker-compose build
docker-compose up -d

# Check service status
echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "=== Installation Complete ==="
echo "API available at: http://localhost:8000"
echo "MCP Server available at: http://localhost:5000"
echo "UI available at: Open ui/index.html in a web browser"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
