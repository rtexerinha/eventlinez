#!/bin/bash

echo "🔍 Troubleshooting 502 Bad Gateway Error"
echo "========================================"

# Check Docker containers status
echo "🐳 Checking Docker containers..."
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        echo "Docker containers:"
        sudo docker ps -a || docker ps -a
        echo ""
        
        echo "Docker Compose services:"
        sudo docker-compose ps || docker-compose ps
        echo ""
        
        # Check if web container is running
        WEB_CONTAINER=$(sudo docker ps --filter "name=web" --format "{{.Names}}" 2>/dev/null || docker ps --filter "name=web" --format "{{.Names}}" 2>/dev/null)
        if [ -n "$WEB_CONTAINER" ]; then
            echo "✅ Web container found: $WEB_CONTAINER"
            echo "Web container logs (last 20 lines):"
            sudo docker logs --tail=20 $WEB_CONTAINER || docker logs --tail=20 $WEB_CONTAINER
            echo ""
        else
            echo "❌ No web container found"
        fi
    else
        echo "❌ Docker daemon not running"
    fi
else
    echo "❌ Docker not available"
fi

# Check what's running on common ports
echo "🔌 Checking port usage..."
echo "Port 8000 (Django default):"
ss -tlnp | grep :8000 || netstat -tlnp | grep :8000 || echo "Nothing on port 8000"

echo "Port 80 (HTTP):"
ss -tlnp | grep :80 || netstat -tlnp | grep :80 || echo "Nothing on port 80"

echo "Port 443 (HTTPS):"
ss -tlnp | grep :443 || netstat -tlnp | grep :443 || echo "Nothing on port 443"

# Check systemctl services
echo ""
echo "🔧 Checking systemctl services..."
systemctl --user status eventlinez 2>/dev/null || echo "No user eventlinez service"
sudo systemctl status eventlinez 2>/dev/null || echo "No system eventlinez service"

# Check Nginx status and config
echo ""
echo "🌐 Checking Nginx..."
sudo systemctl status nginx 2>/dev/null || echo "Nginx status unknown"

echo ""
echo "Nginx configuration test:"
sudo nginx -t 2>/dev/null || echo "Could not test Nginx config"

# Check if we can reach the application directly
echo ""
echo "🏥 Health checks..."
echo "Direct application check (port 8000):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "Could not connect to port 8000"

echo ""
echo "Nginx check (port 80):"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "Could not connect to port 80"

# Check Django specific endpoints
echo ""
echo "Django admin check:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ || echo "Could not connect to Django admin"

# Check environment variables
echo ""
echo "🔧 Environment check..."
echo "USER: $USER"
echo "PWD: $(pwd)"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

# Check if Django can start
echo ""
echo "🐍 Django check..."
if [ -f manage.py ]; then
    echo "Django check (dry run):"
    python manage.py check 2>/dev/null || python3 manage.py check 2>/dev/null || echo "Could not run Django check"
else
    echo "❌ manage.py not found in current directory"
fi

echo ""
echo "📋 Summary:"
echo "- Check Docker containers are running and healthy"
echo "- Verify application is listening on port 8000"
echo "- Ensure Nginx is configured to proxy to correct backend"
echo "- Check for any port conflicts or binding issues"
