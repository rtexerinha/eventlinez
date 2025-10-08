#!/bin/bash
# Script to fix template caching issues on test server

set -e

echo "🔧 Fixing template caching issues on test.eventlinez.com"

# SSH into the test server and execute commands
ssh sunset@test.eventlinez.com << 'ENDSSH'

set -e

echo "📁 Navigating to deployment directory..."
cd /home/sunset/eventlinez

echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "🧹 Step 1: Clear ALL Python bytecode caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

echo "🗑️ Step 2: Clear Django cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('✅ Django cache cleared')" || true

echo "📦 Step 3: Clear pip cache..."
pip cache purge 2>/dev/null || true

echo "🔄 Step 4: Remove and recollect static files..."
rm -rf staticfiles/*
python manage.py collectstatic --noinput --clear

echo "🔍 Step 5: Verify templates are NOT in staticfiles..."
# Check if any .html files were incorrectly collected as static files
if find staticfiles -name "cart.html" -o -name "checkout.html" 2>/dev/null | grep -q .; then
    echo "⚠️ WARNING: HTML templates found in staticfiles! Removing..."
    find staticfiles -name "*.html" -type f -delete
else
    echo "✅ No HTML templates in staticfiles (correct)"
fi

echo "🔄 Step 6: Restart Django application..."
sudo systemctl restart eventlinez.service

echo "⏳ Waiting for service to start..."
sleep 5

echo "🔄 Step 7: Clear nginx cache and restart..."
# Clear nginx cache if it exists
sudo rm -rf /var/cache/nginx/* 2>/dev/null || true

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo "⏳ Waiting for nginx to reload..."
sleep 3

echo "🧪 Step 8: Test the application..."
if curl -f -s http://localhost:8000/cart/ > /dev/null; then
    echo "✅ Application is responding"
else
    echo "⚠️ Application may not be running properly"
    echo "📋 Recent logs:"
    sudo journalctl -u eventlinez.service --no-pager -n 20
fi

echo "✅ Template caching fix completed!"
echo ""
echo "📝 Next steps:"
echo "1. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "2. Test at: http://test.eventlinez.com/cart/"
echo ""
echo "💡 If issue persists, check logs with:"
echo "   sudo journalctl -u eventlinez.service -f"

ENDSSH

echo "🎉 Done! Please test the application now."
