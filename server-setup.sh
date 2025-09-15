#!/bin/bash

# Eventlinez Test Server Initial Setup Script
# Run this script on the test server (45.79.112.247) as user 'sunset'

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_USER="sunset"
APP_NAME="eventlinez"
APP_PATH="/home/sunset/eventlinez"
BACKUP_PATH="/home/sunset/backups"
LOG_PATH="/var/log"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as correct user
if [ "$USER" != "$SERVER_USER" ]; then
    error "This script must be run as user: $SERVER_USER"
    echo "Current user: $USER"
    exit 1
fi

log "🚀 Starting Eventlinez test server setup..."

# Update system packages
log "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y
success "System packages updated"

# Install required packages
log "📦 Installing required packages..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    nginx \
    curl \
    wget \
    unzip \
    htop \
    tree \
    supervisor \
    ufw \
    fail2ban
success "Required packages installed"

# Install optional packages
log "📦 Installing optional packages..."
read -p "Do you want to install PostgreSQL? (y/n): " install_postgres
if [ "$install_postgres" = "y" ] || [ "$install_postgres" = "Y" ]; then
    sudo apt install -y postgresql postgresql-contrib
    success "PostgreSQL installed"
fi

read -p "Do you want to install Docker? (y/n): " install_docker
if [ "$install_docker" = "y" ] || [ "$install_docker" = "Y" ]; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $SERVER_USER
    rm get-docker.sh
    success "Docker installed"
fi

# Create necessary directories
log "📁 Creating application directories..."
mkdir -p $APP_PATH
mkdir -p $BACKUP_PATH
mkdir -p ~/.ssh
success "Directories created"

# Generate SSH key for GitHub Actions
log "🔑 Generating SSH key for GitHub Actions..."
if [ ! -f ~/.ssh/github_actions_key ]; then
    ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key -N ""
    success "SSH key generated"
else
    warning "SSH key already exists"
fi

# Set proper SSH permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_actions_key
chmod 644 ~/.ssh/github_actions_key.pub

# Add public key to authorized_keys
log "🔑 Setting up SSH access..."
if [ -f ~/.ssh/github_actions_key.pub ]; then
    if [ ! -f ~/.ssh/authorized_keys ]; then
        touch ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys
    fi
    
    # Add the key if it's not already there
    if ! grep -q "$(cat ~/.ssh/github_actions_key.pub)" ~/.ssh/authorized_keys 2>/dev/null; then
        cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
        success "SSH key added to authorized_keys"
    else
        warning "SSH key already in authorized_keys"
    fi
fi

# Configure firewall
log "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
success "Firewall configured"

# Configure fail2ban
log "🛡️ Configuring fail2ban..."
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
success "Fail2ban configured"

# Set up log rotation
log "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/eventlinez > /dev/null << EOF
/var/log/eventlinez-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
success "Log rotation configured"

# Clone repository (if GitHub repository is available)
log "📥 Setting up application repository..."
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/eventlinez.git): " repo_url
if [ ! -z "$repo_url" ]; then
    if [ ! -d "$APP_PATH/.git" ]; then
        git clone $repo_url $APP_PATH
        cd $APP_PATH
        git checkout develop
        success "Repository cloned"
    else
        warning "Repository already exists"
    fi
else
    warning "No repository URL provided. You'll need to clone manually later."
fi

# Set up Python virtual environment
if [ -d "$APP_PATH" ]; then
    log "🐍 Setting up Python virtual environment..."
    cd $APP_PATH
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        success "Python dependencies installed"
    else
        warning "requirements.txt not found. Dependencies will be installed during first deployment."
    fi
fi

# Create systemd service template
log "⚙️ Creating systemd service template..."
sudo tee /etc/systemd/system/eventlinez.service > /dev/null << EOF
[Unit]
Description=Eventlinez Django Application
After=network.target

[Service]
Type=simple
User=$SERVER_USER
Group=$SERVER_USER
WorkingDirectory=$APP_PATH
Environment=PATH=$APP_PATH/venv/bin
ExecStart=$APP_PATH/venv/bin/python $APP_PATH/manage.py runserver 0.0.0.0:8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable eventlinez.service
success "Systemd service created"

# Create Nginx configuration
log "🌐 Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/eventlinez > /dev/null << EOF
server {
    listen 80;
    server_name test.eventlinez.com 45.79.112.247;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location /static/ {
        alias $APP_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $APP_PATH/media/;
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
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    client_max_body_size 100M;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/eventlinez /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
success "Nginx configured"

# Create environment file template
if [ -d "$APP_PATH" ]; then
    log "⚙️ Creating environment file template..."
    if [ ! -f "$APP_PATH/.env" ]; then
        cat > $APP_PATH/.env << EOF
# Django Configuration
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=test.eventlinez.com,45.79.112.247,localhost,127.0.0.1

# Database Configuration (SQLite by default)
DATABASE_URL=sqlite:///$APP_PATH/db.sqlite3

# Static and Media Files
STATIC_ROOT=$APP_PATH/staticfiles
MEDIA_ROOT=$APP_PATH/media

# Application Settings
APP_HOST=https://test.eventlinez.com
PROD=True

# Email Configuration (optional)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password

# Stripe Configuration (optional)
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
EOF
        chmod 600 $APP_PATH/.env
        success "Environment file template created"
    else
        warning "Environment file already exists"
    fi
fi

# Set proper permissions
log "🔐 Setting file permissions..."
sudo chown -R $SERVER_USER:$SERVER_USER $APP_PATH $BACKUP_PATH
chmod -R 755 $APP_PATH
if [ -f "$APP_PATH/.env" ]; then
    chmod 600 $APP_PATH/.env
fi
success "Permissions set"

# Display setup summary
log "📊 Setup Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Server: 45.79.112.247 (test.eventlinez.com)"
echo "👤 User: $SERVER_USER"
echo "📂 App Path: $APP_PATH"
echo "💾 Backup Path: $BACKUP_PATH"
echo "🔑 SSH Key: ~/.ssh/github_actions_key"
echo "⚙️ Service: eventlinez.service"
echo "🌐 Nginx: /etc/nginx/sites-available/eventlinez"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

success "✅ Server setup completed!"

echo ""
log "📋 Next Steps:"
echo "1. Copy your SSH keys for GitHub Actions:"
echo "   Public key (add to GitHub repository deploy keys):"
echo "   $(cat ~/.ssh/github_actions_key.pub)"
echo ""
echo "   Private key (add to GitHub Secrets as TEST_SERVER_SSH_KEY):"
echo "   $(cat ~/.ssh/github_actions_key)"
echo ""
echo "2. Update the .env file with your actual configuration:"
echo "   nano $APP_PATH/.env"
echo ""
echo "3. Set up GitHub Secrets in your repository:"
echo "   - TEST_SERVER_HOST: 45.79.112.247"
echo "   - TEST_SERVER_USER: sunset"
echo "   - TEST_SERVER_SSH_KEY: [private key content]"
echo "   - DEPLOY_PATH: /home/sunset"
echo ""
echo "4. Push your code to the develop branch to trigger deployment"
echo ""
echo "🎉 Your server is ready for CI/CD deployment!"
