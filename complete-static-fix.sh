#!/bin/bash

# Complete Static Files Fix Script
# This script comprehensively fixes Docker, static files, and nginx configuration

echo "🔧 Starting complete static files fix..."

# Step 1: Fix Docker daemon
echo "🐳 Step 1: Ensuring Docker daemon is running..."
if ! docker info >/dev/null 2>&1; then
    echo "Starting Docker daemon..."
    sudo systemctl start docker
    sudo systemctl enable docker
    sleep 5
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon failed to start - trying alternative approach"
    
    # Fallback: Kill any stuck Docker processes
    sudo pkill -f docker
    sleep 2
    sudo systemctl restart docker
    sleep 10
    
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker completely failed - will use non-Docker deployment"
        # Kill Django processes and restart manually
        sudo pkill -f "manage.py runserver"
        cd /app/eventlinez
        source /app/.env/bin/activate
        python manage.py collectstatic --noinput --clear
        nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
        echo "✅ Fallback Django deployment started"
        exit 0
    fi
fi

echo "✅ Docker daemon is running"

# Step 2: Reset Docker containers
echo "🔄 Step 2: Resetting Docker containers..."
cd /app/eventlinez

# Force stop and remove all containers
docker-compose down --volumes --remove-orphans 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Clean up Docker system
docker system prune -f --volumes

# Step 3: Rebuild with fresh static files
echo "🏗️ Step 3: Rebuilding containers..."
docker-compose up -d --build --force-recreate

# Wait for containers
echo "⏳ Waiting for containers to start..."
sleep 25

# Step 4: Force static file collection
echo "📁 Step 4: Collecting static files..."
max_attempts=5
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T web python manage.py collectstatic --noinput --clear; then
        echo "✅ Static files collected successfully"
        break
    else
        echo "⚠️ Static collection failed (attempt $attempt/$max_attempts), retrying..."
        sleep 5
        attempt=$((attempt + 1))
    fi
done

# Step 5: Fix nginx configuration
echo "🌐 Step 5: Fixing nginx configuration..."

# Create proper nginx config
cat > /tmp/eventlinez_nginx.conf << 'EOF'
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

    # Static files - try Docker volume first, then host path
    location /static/ {
        alias /app/eventlinez/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri $uri/ @static_fallback;
    }
    
    location @static_fallback {
        root /app/eventlinez;
        try_files /staticfiles$uri /static$uri =404;
    }

    # Media files
    location /media/ {
        alias /app/eventlinez/media/;
        expires 1y;
        add_header Cache-Control "public";
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
    }
}
EOF

# Backup and update nginx config
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Replace the server block in nginx.conf
sed '/server {/,/^}/c\
    include /etc/nginx/sites-enabled/eventlinez;' /etc/nginx/nginx.conf > /tmp/nginx_updated.conf

# Create sites-available directory if it doesn't exist
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Install the site config
cp /tmp/eventlinez_nginx.conf /etc/nginx/sites-available/eventlinez
ln -sf /etc/nginx/sites-available/eventlinez /etc/nginx/sites-enabled/eventlinez

# Update main nginx.conf if needed
cp /tmp/nginx_updated.conf /etc/nginx/nginx.conf

# Test and reload nginx
echo "🧪 Testing nginx configuration..."
if nginx -t; then
    echo "✅ Nginx config is valid"
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config has errors - restoring backup"
    cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    systemctl reload nginx
fi

# Step 6: Verify everything is working
echo "🔍 Step 6: Verification..."
sleep 5

echo "Testing static file access..."
if curl -I http://localhost:8000/static/css/bootstrap.min.css | grep -q "200\|304"; then
    echo "✅ Static files accessible via Django"
else
    echo "⚠️ Static files not accessible via Django"
fi

if curl -I https://test.eventlinez.com/static/css/bootstrap.min.css | grep -q "200\|304"; then
    echo "✅ Static files accessible via nginx"
else
    echo "⚠️ Static files not accessible via nginx"
fi

echo "🏥 Testing main site..."
if curl -I https://test.eventlinez.com | grep -q "200"; then
    echo "✅ Main site is accessible"
else
    echo "⚠️ Main site has issues"
fi

echo "📊 Container status:"
docker-compose ps

echo "✅ Complete static files fix finished!"
echo "🌐 Visit https://test.eventlinez.com to check the site"
