#!/bin/bash
# Docker Installation Script for 3D Room Intelligence System

echo "Installing Docker and Docker Compose..."

# Update package list
sudo apt update

# Install Docker
echo "Installing Docker..."
sudo apt install -y docker.io docker-compose

# Start Docker service
echo "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (to run without sudo)
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

echo ""
echo "✅ Docker installation complete!"
echo ""
echo "⚠️  IMPORTANT: You need to log out and log back in (or run 'newgrp docker')"
echo "   for the docker group changes to take effect."
echo ""
echo "After logging back in, verify installation:"
echo "  docker --version"
echo "  docker-compose --version"
echo ""
echo "Then start the database:"
echo "  docker-compose up -d postgres"


