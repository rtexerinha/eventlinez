#!/bin/bash

echo "🔧 Attempting to fix 502 Bad Gateway error"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f docker-compose.yml ]; then
    echo "❌ docker-compose.yml not found. Please run from the project root."
    exit 1
fi

# Function to use sudo if needed for Docker commands
check_docker_permission() {
    if docker version >/dev/null 2>&1; then
        DOCKER_CMD="docker"
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_CMD="sudo docker"
        DOCKER_COMPOSE_CMD="sudo docker-compose"
    fi
}

echo "🔍 Checking Docker permissions..."
check_docker_permission

# Restart Docker containers
echo "🔄 Restarting Docker containers..."
$DOCKER_COMPOSE_CMD down --timeout 30
sleep 5
$DOCKER_COMPOSE_CMD up -d --build --force-recreate

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 20

# Check container status
echo "🐳 Checking container status..."
$DOCKER_COMPOSE_CMD ps

# Check if web container is healthy
echo "🏥 Checking web container health..."
WEB_CONTAINER=$($DOCKER_CMD ps --filter "name=web" --format "{{.Names}}" | head -1)
if [ -n "$WEB_CONTAINER" ]; then
    echo "✅ Web container: $WEB_CONTAINER"
    echo "Container logs (last 10 lines):"
    $DOCKER_CMD logs --tail=10 $WEB_CONTAINER
    
    # Test if Django is responding inside the container
    echo ""
    echo "🧪 Testing Django inside container..."
    $DOCKER_COMPOSE_CMD exec -T web python -c "
import requests
try:
    response = requests.get('http://localhost:8000/')
    print(f'Django response: {response.status_code}')
except Exception as e:
    print(f'Django error: {e}')
" 2>/dev/null || echo "Could not test Django inside container"
else
    echo "❌ No web container found"
fi

# Check port bindings
echo ""
echo "🔌 Checking port bindings..."
$DOCKER_CMD ps --format "table {{.Names}}\t{{.Ports}}"

# Restart Nginx
echo ""
echo "🌐 Restarting Nginx..."
sudo systemctl restart nginx 2>/dev/null || echo "Could not restart Nginx"
sleep 2

# Test connections
echo ""
echo "🧪 Testing connections..."
echo "Direct Django (port 8000):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "FAIL")
echo "Response: $HTTP_CODE"

echo ""
echo "Via Nginx (port 80):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "FAIL")
echo "Response: $HTTP_CODE"

# Show next steps
echo ""
echo "📋 Next steps if still failing:"
echo "1. Run: sudo systemctl status nginx"
echo "2. Check: sudo tail -f /var/log/nginx/error.log"
echo "3. Verify Nginx config: sudo nginx -t"
echo "4. Check application logs: $DOCKER_COMPOSE_CMD logs web"
echo "5. Ensure port 8000 is accessible: curl http://localhost:8000/"
