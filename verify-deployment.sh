#!/bin/bash

# Deployment Verification Script for test.eventlinez.com
# Run this script to verify your deployment status and troubleshoot version issues

echo "🔍 EventLinEZ Deployment Verification"
echo "======================================"

# Check current branch and commit
echo "📋 Local Git Status:"
echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git rev-parse HEAD)"
echo "Short commit: $(git rev-parse --short HEAD)"
echo "Last commit message: $(git log -1 --pretty=%B | head -n1)"
echo ""

# Check if changes are committed
echo "📝 Uncommitted Changes:"
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ You have uncommitted changes:"
    git status --short
    echo ""
    echo "💡 Commit your changes first: git add . && git commit -m 'Your message'"
else
    echo "✅ No uncommitted changes"
fi
echo ""

# Check if changes are pushed
echo "📤 Push Status:"
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git ls-remote origin develop | cut -f1)

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo "✅ Local and remote commits match"
    echo "Remote commit: $REMOTE_COMMIT"
else
    echo "❌ Local and remote commits don't match"
    echo "Local commit:  $LOCAL_COMMIT"
    echo "Remote commit: $REMOTE_COMMIT"
    echo ""
    echo "💡 Push your changes: git push origin develop"
fi
echo ""

# Check GitHub Actions status
echo "🔄 GitHub Actions Status:"
echo "Check your workflow at: https://github.com/YOUR_USERNAME/eventlinez/actions"
echo ""

# Test server version (if accessible)
echo "🌐 Server Version Check:"
if curl -s https://test.eventlinez.com/static/version_info.json > /tmp/server_version.json 2>/dev/null; then
    echo "✅ Server version info found:"
    cat /tmp/server_version.json | python3 -m json.tool
    
    # Compare commits
    SERVER_COMMIT=$(cat /tmp/server_version.json | python3 -c "import sys, json; print(json.load(sys.stdin)['commit_sha'])" 2>/dev/null)
    if [ "$LOCAL_COMMIT" = "$SERVER_COMMIT" ]; then
        echo "✅ Server and local commits match!"
    else
        echo "❌ Server and local commits don't match"
        echo "This indicates a deployment issue"
    fi
else
    echo "⚠️ Could not retrieve server version info"
    echo "This might mean:"
    echo "  - Deployment hasn't completed yet"
    echo "  - Version info file wasn't created"
    echo "  - Server is not accessible"
fi
echo ""

# Manual deployment commands
echo "🛠️ Manual Deployment Commands:"
echo "If automatic deployment failed, try these commands on the server:"
echo ""
echo "ssh your-user@your-server"
echo "cd /path/to/your/app/eventlinez"
echo "git fetch --all"
echo "git reset --hard origin/develop"
echo "git clean -fd"
echo ""
echo "# Clear all caches"
echo "find . -name '*.pyc' -delete"
echo "find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"
echo "python manage.py shell -c \"from django.core.cache import cache; cache.clear()\""
echo ""
echo "# Restart services"
echo "docker-compose down && docker-compose up -d --build"
echo "# OR for traditional deployment:"
echo "systemctl --user restart eventlinez"
echo ""

# Cleanup
rm -f /tmp/server_version.json

echo "🏁 Verification Complete"
echo ""
echo "💡 Tips for successful deployments:"
echo "1. Always commit and push your changes"
echo "2. Check GitHub Actions for deployment status"
echo "3. Wait 2-3 minutes after push for deployment to complete"
echo "4. Clear your browser cache after deployment"
echo "5. Use hard refresh (Ctrl+F5 or Cmd+Shift+R)"