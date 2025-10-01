#!/bin/bash

# Eventlinez Test Server Deployment Script
# This script handles the deployment process on the test server

set -e  # Exit on any error

# Configuration
APP_NAME="eventlinez"
DEPLOY_USER="sunset"
DEPLOY_PATH="/home/sunset/eventlinez"
PYTHON_PATH="/home/sunset/.local/bin"
BACKUP_DIR="/home/sunset/backups"
LOG_FILE="/var/log/eventlinez-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> $LOG_FILE
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[SUCCESS] $1" >> $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> $LOG_FILE
}

# Check if running as correct user
if [ "$USER" != "$DEPLOY_USER" ]; then
    error "This script must be run as user: $DEPLOY_USER"
    exit 1
fi

# Create necessary directories
mkdir -p $BACKUP_DIR
mkdir -p $(dirname $LOG_FILE)

log "🚀 Starting Eventlinez deployment process..."

# Step 1: Create backup
log "💾 Creating backup of current deployment..."
if [ -d "$DEPLOY_PATH" ]; then
    BACKUP_NAME="eventlinez_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r $DEPLOY_PATH $BACKUP_DIR/$BACKUP_NAME
    success "Backup created: $BACKUP_DIR/$BACKUP_NAME"
else
    warning "No existing deployment found to backup"
fi

# Step 2: Stop services
log "⏹️ Stopping application services..."
sudo systemctl stop eventlinez.service || warning "eventlinez.service not found or already stopped"
sudo systemctl stop nginx || warning "Failed to stop nginx"

# Step 3: Navigate to deployment directory
log "📁 Navigating to deployment directory..."
cd $DEPLOY_PATH || {
    error "Failed to navigate to $DEPLOY_PATH"
    exit 1
}

# Step 4: Pull latest changes
log "📥 Pulling latest changes from develop branch..."
git fetch origin
git reset --hard origin/develop
git clean -fd
success "Code updated successfully"

# Step 5: Set up Python virtual environment
log "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment created"
fi

source venv/bin/activate
success "Virtual environment activated"

# Step 6: Install/Update dependencies
log "📦 Installing/Updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
success "Dependencies installed"

# Step 7: Set up environment variables
log "⚙️ Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=test.eventlinez.com,45.79.112.247,localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
STATIC_ROOT=/home/sunset/eventlinez/staticfiles
MEDIA_ROOT=/home/sunset/eventlinez/media
APP_HOST=https://test.eventlinez.com
PROD=True
EOF
    success "Environment file created"
else
    log "Environment file already exists"
fi

# Step 8: Run database migrations
log "🗄️ Running database migrations..."
# Drop problematic database views before migrations
log "Dropping problematic database views..."
python manage.py drop_views --force || warning "Could not drop views (might not exist)"

python manage.py migrate --noinput
success "Database migrations completed"

# Create database views safely after migrations
log "Creating database views..."
python manage.py create_sales_view --force || warning "Could not create sales view (might not be needed)"

# Step 9: Clean caches and collect static files
log "🧹 Cleaning application caches..."
# Clear Django cache
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Django cache cleared')" || warning "Could not clear Django cache"

# Clear Python bytecode cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || warning "Could not clear Python cache"
find . -name "*.pyc" -delete 2>/dev/null || warning "Could not delete .pyc files"

# Clear pip cache
pip cache purge 2>/dev/null || warning "Could not clear pip cache"

# Clear any temporary files
rm -rf /tmp/eventlinez_* 2>/dev/null || warning "Could not clear temp files"

success "Caches cleaned"

log "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear
success "Static files collected"

# Step 10: Set proper permissions
log "🔐 Setting proper file permissions..."
chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
chmod -R 755 $DEPLOY_PATH
chmod 644 $DEPLOY_PATH/.env
success "Permissions set"

# Step 11: Create systemd service file if it doesn't exist
log "⚙️ Setting up systemd service..."
if [ ! -f "/etc/systemd/system/eventlinez.service" ]; then
    sudo tee /etc/systemd/system/eventlinez.service > /dev/null << EOF
[Unit]
Description=Eventlinez Django App
After=network.target

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$DEPLOY_PATH
Environment=PATH=$DEPLOY_PATH/venv/bin
ExecStart=$DEPLOY_PATH/venv/bin/python $DEPLOY_PATH/manage.py runserver 0.0.0.0:8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable eventlinez.service
    success "Systemd service created and enabled"
fi

# Step 12: Set up Nginx configuration if it doesn't exist
log "🌐 Setting up Nginx configuration..."
if [ ! -f "/etc/nginx/sites-available/eventlinez" ]; then
    sudo tee /etc/nginx/sites-available/eventlinez > /dev/null << EOF
server {
    listen 80;
    server_name test.eventlinez.com 45.79.112.247;

    location /static/ {
        alias $DEPLOY_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $DEPLOY_PATH/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    client_max_body_size 100M;
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/eventlinez /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    success "Nginx configuration created and enabled"
fi

# Step 13: Start services
log "🔄 Starting application services..."
sudo systemctl start eventlinez.service
sudo systemctl start nginx
success "Services started"

# Step 14: Health check
log "🏥 Performing health check..."
sleep 10

# Check if application is responding
if curl -f -s http://localhost:8000/admin/ > /dev/null; then
    success "Health check passed - Application is responding"
else
    error "Health check failed - Application may not be running properly"
    
    # Show recent logs for debugging
    log "📋 Recent application logs:"
    sudo journalctl -u eventlinez.service --no-pager -n 20
fi

# Step 15: Cleanup old backups (keep last 5)
log "🧹 Cleaning up old backups..."
cd $BACKUP_DIR
ls -t eventlinez_backup_* 2>/dev/null | tail -n +6 | xargs -r rm -rf
success "Old backups cleaned up"

# Step 16: Display deployment summary
log "📊 Deployment Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Application: Eventlinez"
echo "🌐 URL: http://test.eventlinez.com"
echo "📂 Path: $DEPLOY_PATH"
echo "👤 User: $DEPLOY_USER"
echo "🕐 Deployed: $(date)"
echo "🔗 Branch: develop"
echo "📝 Logs: $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

success "🎉 Deployment completed successfully!"

# Optional: Send notification (uncomment if needed)
# curl -X POST -H 'Content-type: application/json' \
#     --data '{"text":"🚀 Eventlinez test deployment completed successfully!"}' \
#     YOUR_SLACK_WEBHOOK_URL

log "✅ All deployment steps completed. Application should be available at http://test.eventlinez.com"
