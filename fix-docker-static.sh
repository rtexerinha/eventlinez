#!/bin/bash

# Fix Docker and Static Files Script
# This script restarts Docker daemon and rebuilds containers with proper static file serving

echo "🔧 Fixing Docker daemon and static file serving issues..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "🐳 Starting Docker daemon..."
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Wait for Docker to start
    sleep 5
    
    # Check again
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Failed to start Docker daemon"
        exit 1
    fi
fi

echo "✅ Docker daemon is running"

# Navigate to application directory
cd /app/eventlinez

# Stop existing containers
echo "⏹️ Stopping existing containers..."
docker-compose down || echo "No containers to stop"

# Clean up Docker resources
echo "🧹 Cleaning Docker resources..."
docker system prune -f --volumes

# Rebuild and start containers
echo "🏗️ Rebuilding containers..."
docker-compose up -d --build --force-recreate

# Wait for containers to be ready
echo "⏳ Waiting for containers to start..."
sleep 20

# Check container status
echo "🔍 Checking container status..."
docker-compose ps

# Force static file collection
echo "📁 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput --clear

# Restart nginx to pick up any changes
echo "🔄 Restarting nginx..."
sudo systemctl restart nginx

# Test static file serving
echo "🧪 Testing static file access..."
curl -I http://localhost:8000/static/css/bootstrap.min.css || echo "Static files still not accessible via Django"

echo "✅ Docker and static files fix completed!"
echo "🌐 Check https://test.eventlinez.com to verify the site is working"
