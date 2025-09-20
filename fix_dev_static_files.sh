#!/bin/bash

# Fix Static Files on Development Server (test.eventlinez.com)
# Run this script as the sunset user, then sudo to root for file operations

echo "🔧 FIXING STATIC FILE SERVING ON DEVELOPMENT SERVER"
echo "=================================================="

# Check current directory
echo "📍 Current directory: $(pwd)"

# Go to the application directory
cd /app/eventlinez || {
    echo "❌ Error: Cannot find /app/eventlinez directory"
    exit 1
}

echo "📁 Working in: $(pwd)"

# Activate virtual environment
source /app/.venv/bin/activate || {
    echo "❌ Error: Cannot activate virtual environment"
    exit 1
}

echo "🐍 Virtual environment activated"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Check if staticfiles directory was created
if [ -d "/app/eventlinez/staticfiles" ]; then
    echo "✅ Static files collected to: /app/eventlinez/staticfiles"
    echo "📊 Static files count: $(find /app/eventlinez/staticfiles -type f | wc -l)"
else
    echo "❌ Error: Static files directory not created"
    exit 1
fi

# Set proper permissions for static files
echo "🔐 Setting permissions for static files..."
sudo chown -R nginx:nginx /app/eventlinez/staticfiles
sudo chmod -R 755 /app/eventlinez/staticfiles

# Also ensure media files have correct permissions
if [ -d "/app/media" ]; then
    echo "🔐 Setting permissions for media files..."
    sudo chown -R nginx:nginx /app/media
    sudo chmod -R 755 /app/media
fi

# Check Nginx configuration for static files
echo "🔍 Checking Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart uwsgi
sudo systemctl restart nginx

echo ""
echo "🧪 TESTING STATIC FILE SERVING..."
echo "================================="

# Test CSS file
css_status=$(curl -s -o /dev/null -w "%{http_code}" "https://test.eventlinez.com/static/css/bootstrap.min.css")
echo "CSS file status: $css_status"

# Test JS file  
js_status=$(curl -s -o /dev/null -w "%{http_code}" "https://test.eventlinez.com/static/js/bootstrap.min.js")
echo "JS file status: $js_status"

# Test image file
img_status=$(curl -s -o /dev/null -w "%{http_code}" "https://test.eventlinez.com/static/img/Eventlinez.png")
echo "Image file status: $img_status"

echo ""
if [ "$css_status" = "200" ] && [ "$js_status" = "200" ] && [ "$img_status" = "200" ]; then
    echo "🎉 SUCCESS! Static files are now being served correctly!"
    echo ""
    echo "✅ WHAT WAS FIXED:"
    echo "1. Collected all static files using Django's collectstatic"
    echo "2. Set proper ownership (nginx:nginx) for static and media directories"
    echo "3. Set proper permissions (755) for file access"
    echo "4. Restarted uWSGI and Nginx services"
    echo ""
    echo "🌐 Your website at test.eventlinez.com should now load with proper styling!"
else
    echo "❌ STILL HAVING ISSUES:"
    echo "Some static files are still not accessible. Manual investigation needed."
    echo ""
    echo "🔍 DEBUG STEPS:"
    echo "1. Check Nginx error logs: sudo tail -f /var/log/nginx/error.log"
    echo "2. Verify static files exist: ls -la /app/eventlinez/staticfiles/"
    echo "3. Check Nginx static file configuration in your site config"
fi

echo ""
echo "📝 NEXT STEPS:"
echo "1. Visit https://test.eventlinez.com to verify the page loads properly"
echo "2. Check browser developer tools for any remaining 404 errors"
echo "3. If issues persist, check Nginx logs for specific errors"
