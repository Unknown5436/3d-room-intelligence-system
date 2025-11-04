#!/bin/bash
# Automated Next Steps Script for 3D Room Intelligence System
# Run this script to complete the setup

set -e  # Exit on error

echo "=========================================="
echo "3D Room Intelligence System - Setup"
echo "=========================================="
echo ""

# Step 1: Check Docker
echo "Step 1: Checking Docker installation..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose are installed"
    docker --version
    docker-compose --version
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "✅ Docker is installed (using 'docker compose' command)"
    docker --version
    docker compose version
else
    echo "❌ Docker not found. Installing..."
    echo ""
    echo "Please run the following commands (requires sudo password):"
    echo "  sudo apt update"
    echo "  sudo apt install -y docker.io docker-compose"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
    echo "  sudo usermod -aG docker $USER"
    echo ""
    echo "Then log out and log back in, or run: newgrp docker"
    echo ""
    exit 1
fi

# Check if user is in docker group
if groups | grep -q docker; then
    echo "✅ User is in docker group"
else
    echo "⚠️  User not in docker group. You may need to use 'sudo' for docker commands"
    echo "   Or run: sudo usermod -aG docker $USER && newgrp docker"
fi

echo ""
echo "Step 2: Starting PostgreSQL database..."
docker-compose up -d postgres 2>&1 || docker compose up -d postgres 2>&1

echo ""
echo "Waiting for database to be ready..."
sleep 5

# Check database status
echo ""
echo "Checking database status..."
docker-compose ps 2>&1 || docker compose ps 2>&1

echo ""
echo "Waiting additional time for database initialization..."
sleep 15

echo ""
echo "Step 3: Running test suite..."
echo ""

# Activate virtual environment and run tests
source venv311/bin/activate 2>/dev/null || true
pytest -v

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start API: docker-compose up"
echo "  2. Test upload: curl -X POST \"http://localhost:8000/api/upload-scan\" -F \"file=@Room scan v1.ply\""
echo ""


