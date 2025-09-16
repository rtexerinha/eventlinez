#!/bin/bash

# Complete Nginx Static Files Fix
# Run this script on the server to fix static file serving

echo "🔧 Fixing nginx configuration for static files..."

# Check if running as the right user
if [ "$USER" != "sunset" ] && [ "$USER" != "root" ]; then
    echo "⚠️ Please run this script as 'sunset' user"
    echo "Usage: ssh sunset@45.79.112.247 'bash -s' < fix-nginx-complete.sh"
    exit 1
fi

# Navigate to app directory
cd /app/eventlinez

# Check Docker status first
echo "🐳 Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "🔄 Starting Docker daemon..."
    sudo systemctl start docker
    sleep 5
fi

if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
    
    # Ensure containers are up
    echo "🏗️ Ensuring containers are running..."
    docker-compose up -d
    sleep 10
    
    # Force collect static files
    echo "📁 Collecting static files in Docker..."
    docker-compose exec -T web python manage.py collectstatic --noinput --clear
    
    # Check static files in container
    echo "🔍 Checking static files in container..."
    docker-compose exec -T web ls -la /app/staticfiles/css/ || echo "No CSS files in container"
    
else
    echo "⚠️ Docker not available, using traditional approach..."
    
    # Activate virtual environment and collect static files
    source /app/.env/bin/activate
    python manage.py collectstatic --noinput --clear
fi

# Check static files on host
echo "📂 Checking static files on host system..."
if [ -d "/app/eventlinez/staticfiles" ]; then
    echo "✅ Static files directory exists on host"
    echo "📋 CSS files:"
    ls -la /app/eventlinez/staticfiles/css/ 2>/dev/null || echo "No CSS directory"
else
    echo "❌ Static files directory missing on host"
    echo "Creating directory..."
    mkdir -p /app/eventlinez/staticfiles
    chmod 755 /app/eventlinez/staticfiles
fi

# Create proper nginx configuration
echo "🌐 Creating nginx configuration..."

# Backup current nginx config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Create new server block configuration
sudo tee /etc/nginx/sites-available/eventlinez > /dev/null << 'EOF'
server {
    listen 80;
    server_name test.eventlinez.com 45.79.112.247;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name test.eventlinez.com 45.79.112.247;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/test.eventlinez.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/test.eventlinez.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Static files
    location /static/ {
        alias /app/eventlinez/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
        
        # Try multiple locations for static files
        try_files $uri $uri/ @static_fallback;
    }
    
    # Fallback for static files
    location @static_fallback {
        # Try serving directly from Django if nginx can't find the file
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Media files
    location /media/ {
        alias /app/eventlinez/media/;
        expires 1y;
        add_header Cache-Control "public";
        access_log off;
        try_files $uri $uri/ =404;
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        proxy_buffering off;
    }
}
EOF

# Enable the site
sudo mkdir -p /etc/nginx/sites-enabled
sudo ln -sf /etc/nginx/sites-available/eventlinez /etc/nginx/sites-enabled/

# Remove default nginx config that might conflict
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    
    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration has errors"
    echo "🔙 Restoring backup..."
    sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    sudo systemctl reload nginx
    exit 1
fi

# Test static file serving
echo "🧪 Testing static file access..."
sleep 3

echo "Testing local static file access..."
curl -I http://localhost/static/css/bootstrap.min.css || echo "Local static test failed"

echo "Testing HTTPS static file access..."
curl -I https://test.eventlinez.com/static/css/bootstrap.min.css || echo "HTTPS static test failed"

echo "Testing main site..."
curl -I https://test.eventlinez.com/ || echo "Main site test failed"

echo "✅ Nginx static files fix completed!"
echo ""
echo "📋 Summary:"
echo "  - Static files directory: /app/eventlinez/staticfiles/"
echo "  - Nginx config: /etc/nginx/sites-available/eventlinez"
echo "  - Test URL: https://test.eventlinez.com/static/css/bootstrap.min.css"
echo ""
echo "🌐 Visit https://test.eventlinez.com to check if CSS is now loading"
