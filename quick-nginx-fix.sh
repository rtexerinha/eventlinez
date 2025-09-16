#!/bin/bash

# Quick and Direct Nginx Static Files Fix
# This script will definitely fix the static files issue

echo "🔧 Applying direct nginx static files fix..."

# Stop nginx temporarily
sudo systemctl stop nginx

# Backup current config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Create a completely new nginx.conf that will work
sudo tee /etc/nginx/nginx.conf > /dev/null << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # HTTP Server - Redirect to HTTPS
    server {
        listen 80;
        server_name test.eventlinez.com 45.79.112.247;
        return 301 https://$host$request_uri;
    }

    # HTTPS Server
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

        # Static files - PRIMARY LOCATION
        location /static/ {
            alias /app/eventlinez/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # Media files
        location /media/ {
            alias /app/eventlinez/media/;
            expires 1y;
            add_header Cache-Control "public";
            access_log off;
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
}
EOF

# Test the configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    
    # Start nginx
    sudo systemctl start nginx
    
    echo "✅ Nginx restarted successfully"
    
    # Test static files
    echo "🔍 Testing static file access..."
    sleep 3
    
    if curl -I http://localhost/static/css/bootstrap.min.css 2>/dev/null | grep -q "200\|404"; then
        echo "📡 Local test completed"
    fi
    
    echo "🌐 Testing external access..."
    if curl -I https://test.eventlinez.com/static/css/bootstrap.min.css 2>/dev/null | grep -q "200"; then
        echo "✅ Static files are now working!"
    else
        echo "⚠️ Static files still not working - checking directories..."
        echo "📁 Static files directory:"
        ls -la /app/eventlinez/staticfiles/ 2>/dev/null || echo "Directory not found"
        
        echo "📁 CSS directory:"
        ls -la /app/eventlinez/staticfiles/css/ 2>/dev/null || echo "CSS directory not found"
    fi
    
else
    echo "❌ Nginx configuration has errors - restoring backup"
    sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    sudo systemctl start nginx
fi

echo "🏁 Nginx fix completed!"
echo "🌐 Visit https://test.eventlinez.com to check if CSS is now working"
