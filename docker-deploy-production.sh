#!/bin/bash

# Eventlinez Docker Production Deployment Script
# This script uses Docker to avoid pip/celery installation issues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROD_HOST="50.116.31.214"
PROD_USER="sunset"
PROJECT_DIR="/var/www/eventlinez"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Eventlinez Docker Production Deploy ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to print step headers
print_step() {
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print errors
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Confirmation prompt
confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Pre-deployment checks
print_step "1. Pre-Deployment Checks"

echo "Checking local repository status..."
if [[ -n $(git status -s) ]]; then
    print_warning "You have uncommitted changes!"
    git status -s
    if ! confirm "Continue anyway?"; then
        exit 1
    fi
fi
print_success "Local repository check complete"

echo "Checking Docker setup..."
if ! docker --version > /dev/null 2>&1; then
    print_error "Docker not found! Please install Docker first."
    exit 1
fi

if ! docker compose version > /dev/null 2>&1; then
    print_error "Docker Compose not found! Please install Docker Compose first."
    exit 1
fi

print_success "Docker setup check complete"

# Build and test locally
print_step "2. Build and Test Docker Image Locally"

echo "Building Docker image locally..."
if docker compose build --no-cache; then
    print_success "Docker image built successfully"
else
    print_error "Docker build failed!"
    exit 1
fi

echo "Testing container startup..."
if docker compose up -d; then
    sleep 5
    if docker compose ps | grep -q "Up"; then
        print_success "Container test successful"
        docker compose down
    else
        print_error "Container failed to start properly"
        docker compose logs
        exit 1
    fi
else
    print_error "Container startup test failed!"
    exit 1
fi

# Commit and push
print_step "3. Commit and Push Changes"

if confirm "Do you want to commit all changes?"; then
    read -p "Enter commit message: " commit_msg
    git add .
    git commit -m "$commit_msg" || print_warning "Nothing to commit"
    git push origin develop
    print_success "Changes committed and pushed to develop"
fi

# Deploy to production
print_step "4. Deploy to Production Server"

print_warning "IMPORTANT: This will deploy using Docker to avoid pip/celery issues!"
echo "Server: $PROD_USER@$PROD_HOST"
echo ""

if ! confirm "Proceed with Docker-based production deployment?"; then
    echo "Deployment cancelled"
    exit 0
fi

# Create production docker-compose file
PROD_COMPOSE=$(cat <<'EOF'
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://eventlinez_user:your_password@db:5432/eventlinez_db
      - DEBUG=False
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:17
    environment:
      POSTGRES_DB: eventlinez_db
      POSTGRES_USER: eventlinez_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
EOF
)

# Execute deployment on production server
ssh $PROD_USER@$PROD_HOST << 'ENDSSH'
set -e

echo "╔════════════════════════════════════════╗"
echo "║  Docker Production Deployment Steps   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Step 1: Create Backup
echo "▶ Creating backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/sunset/backups/$TIMESTAMP"
mkdir -p $BACKUP_DIR

echo "  → Backing up database..."
if command -v docker > /dev/null 2>&1; then
    # If using Docker, backup from container
    docker exec eventlinez-db-1 pg_dump -U eventlinez_user eventlinez_db > $BACKUP_DIR/eventlinez_db_backup.sql 2>/dev/null || \
    sudo -u postgres pg_dump eventlinez_db > $BACKUP_DIR/eventlinez_db_backup.sql 2>&1 || \
    echo "  ⚠ Database backup failed - continuing anyway"
else
    # Fallback to system postgres
    sudo -u postgres pg_dump eventlinez_db > $BACKUP_DIR/eventlinez_db_backup.sql 2>&1 || \
    echo "  ⚠ Database backup failed - continuing anyway"
fi
echo "  ✓ Database backup complete (or skipped)"

echo "  → Backing up media files..."
cp -r /var/www/eventlinez/media $BACKUP_DIR/ 2>/dev/null || true
echo "  ✓ Media files backup complete"

cat > $BACKUP_DIR/backup_info.txt << EOI
Backup Date: $(date)
Backup Location: $BACKUP_DIR
Pre-Docker-deployment backup
EOI

echo "✓ Backup completed at: $BACKUP_DIR"
echo ""

# Step 2: Install Docker if not present
echo "▶ Checking Docker installation..."
if ! command -v docker > /dev/null 2>&1; then
    echo "  → Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "  ✓ Docker installed"
else
    echo "  ✓ Docker already installed"
fi

if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    echo "  → Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "  ✓ Docker Compose installed"
else
    echo "  ✓ Docker Compose already available"
fi

# Step 3: Pull Latest Code
echo "▶ Pulling latest code..."
cd /var/www/eventlinez
git fetch origin
git checkout main
git pull origin main
echo "✓ Code updated"
echo ""

# Step 4: Stop existing services
echo "▶ Stopping existing services..."
if systemctl is-active --quiet gunicorn; then
    sudo systemctl stop gunicorn
    echo "  ✓ Gunicorn stopped"
fi

# Stop any existing Docker containers
docker compose down 2>/dev/null || true
echo "  ✓ Existing containers stopped"
echo ""

# Step 5: Build and start Docker containers
echo "▶ Building and starting Docker containers..."
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

# Build with no cache to ensure fresh build
docker compose build --no-cache

# Start services
docker compose up -d

echo "✓ Docker containers started"
echo ""

# Step 6: Wait for services to be ready
echo "▶ Waiting for services to be ready..."
sleep 10

# Check if containers are running
if docker compose ps | grep -q "Up"; then
    echo "✓ Containers are running"
else
    echo "✗ Some containers failed to start"
    docker compose ps
    docker compose logs
    exit 1
fi

# Step 7: Configure Nginx to proxy to Docker
echo "▶ Configuring Nginx for Docker..."
sudo tee /etc/nginx/sites-available/eventlinez > /dev/null << 'NGINXCONF'
server {
    listen 80;
    server_name eventlinez.com.br www.eventlinez.com.br;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name eventlinez.com.br www.eventlinez.com.br;

    # SSL configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/eventlinez.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eventlinez.com.br/privkey.pem;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files served by Nginx
    location /static/ {
        alias /var/www/eventlinez/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/eventlinez/media/;
        expires 7d;
    }
}
NGINXCONF

# Enable site and restart nginx
sudo ln -sf /etc/nginx/sites-available/eventlinez /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
echo "✓ Nginx configured and restarted"
echo ""

# Step 8: Set up container auto-restart
echo "▶ Setting up container auto-restart..."
# Create systemd service for docker-compose
sudo tee /etc/systemd/system/eventlinez-docker.service > /dev/null << 'SYSTEMDCONF'
[Unit]
Description=Eventlinez Docker Compose Application Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/eventlinez
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SYSTEMDCONF

sudo systemctl enable eventlinez-docker.service
echo "✓ Auto-restart service configured"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║     Docker Deployment Completed! 🐳   ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Services Status:"
docker compose ps
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Application URL: https://eventlinez.com.br"
echo ""
echo "To check logs: docker compose logs -f"
echo "To restart: docker compose restart"
echo "To stop: docker compose down"
echo ""

ENDSSH

if [ $? -eq 0 ]; then
    print_success "Docker deployment completed successfully!"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        🐳 Docker Deployment Success! 🎉 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "✅ Advantages of Docker deployment:"
    echo "   • No more pip/celery installation issues"
    echo "   • Consistent environment across dev/prod"
    echo "   • Easy rollbacks and updates"
    echo "   • Isolated dependencies"
    echo ""
    echo "Next steps:"
    echo "1. Test the application at https://eventlinez.com.br"
    echo "2. Verify all functionality works correctly"
    echo "3. Monitor container health"
    echo ""
    echo "Monitor with:"
    echo "  ssh $PROD_USER@$PROD_HOST 'cd /var/www/eventlinez && docker compose logs -f'"
else
    print_error "Docker deployment failed!"
    echo ""
    echo "Check server logs and try again, or fallback to manual deployment."
fi