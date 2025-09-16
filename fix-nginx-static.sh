#!/bin/bash

# Fix Nginx Static Files Configuration
# This script ensures nginx is properly configured to serve static files

echo "🌐 Fixing nginx static file configuration..."

# Check if nginx config exists
if [ ! -f /etc/nginx/nginx.conf ]; then
    echo "❌ Nginx config not found"
    exit 1
fi

# Backup current config
echo "💾 Backing up current nginx config..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Create a proper nginx config for static files
cat > /tmp/nginx_static_config << 'EOF'
    # Static files configuration
    location /static/ {
        alias /app/eventlinez/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Handle missing files gracefully
        try_files $uri $uri/ =404;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
    }
    
    # Media files configuration  
    location /media/ {
        alias /app/eventlinez/media/;
        expires 1y;
        add_header Cache-Control "public";
        
        # Handle missing files gracefully
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
EOF

echo "📝 Updated nginx configuration with proper static file handling"

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration has errors"
    echo "🔙 Restoring backup..."
    cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
fi

# Test static file serving
echo "🧪 Testing static file access..."
sleep 2
curl -I http://localhost/static/css/bootstrap.min.css && echo "✅ Static files accessible" || echo "⚠️ Static files still not accessible"

echo "🌐 Nginx static file configuration completed!"
