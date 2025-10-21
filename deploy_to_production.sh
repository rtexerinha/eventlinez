#!/bin/bash

# Eventlinez Production Deployment Script
# Usage: ./deploy_to_production.sh

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
BACKUP_DIR="/home/sunset/backups"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Eventlinez Production Deployment    ║${NC}"
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

echo ""
echo "Checking Docker containers..."
if docker compose ps | grep -q "Up"; then
    print_success "Docker containers are running"
else
    print_warning "Docker containers are not running"
fi

# Commit and push
print_step "2. Commit and Push Changes"

if confirm "Do you want to commit all changes?"; then
    read -p "Enter commit message: " commit_msg
    git add .
    git commit -m "$commit_msg" || print_warning "Nothing to commit"
    git push origin develop
    print_success "Changes committed and pushed to develop"
fi

# Merge to main
print_step "3. Merge to Main Branch"

if confirm "Merge develop to main branch?"; then
    git checkout main
    git merge develop
    git push origin main
    print_success "Merged to main and pushed"
    git checkout develop
fi

# Create backup script for production
print_step "4. Prepare Backup Script"

BACKUP_SCRIPT=$(cat <<'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/sunset/backups/$TIMESTAMP"
mkdir -p $BACKUP_DIR

echo "Creating backup at: $BACKUP_DIR"

# Backup database
sudo -u postgres pg_dump eventlinez_db > $BACKUP_DIR/eventlinez_db_backup.sql

# Backup media files
cp -r /var/www/eventlinez/media $BACKUP_DIR/ 2>/dev/null || true

# Backup environment file
cp /var/www/eventlinez/.env $BACKUP_DIR/.env.backup 2>/dev/null || true

# Create backup info file
cat > $BACKUP_DIR/backup_info.txt << EOI
Backup Date: $(date)
Backup By: $USER
Reason: Pre-deployment backup before $(date +%Y-%m-%d) deployment
EOI

echo "✓ Backup completed: $BACKUP_DIR"
echo $BACKUP_DIR
EOF
)

# Deploy to production
print_step "5. Deploy to Production Server"

print_warning "IMPORTANT: Make sure you have SSH access to the production server!"
echo "Server: $PROD_USER@$PROD_HOST"
echo ""

if ! confirm "Proceed with production deployment?"; then
    echo "Deployment cancelled"
    exit 0
fi

# Execute deployment on production server
ssh $PROD_USER@$PROD_HOST << 'ENDSSH'
set -e

echo "╔════════════════════════════════════════╗"
echo "║  Production Server Deployment Steps   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Step 1: Create Backup
echo "▶ Creating backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/sunset/backups/$TIMESTAMP"
mkdir -p $BACKUP_DIR

echo "  → Backing up database..."
sudo -u postgres pg_dump eventlinez_db > $BACKUP_DIR/eventlinez_db_backup.sql 2>&1
echo "  ✓ Database backup complete"

echo "  → Backing up media files..."
cp -r /var/www/eventlinez/media $BACKUP_DIR/ 2>/dev/null || true
echo "  ✓ Media files backup complete"

echo "  → Backing up environment file..."
cp /var/www/eventlinez/.env $BACKUP_DIR/.env.backup 2>/dev/null || true
echo "  ✓ Environment file backup complete"

cat > $BACKUP_DIR/backup_info.txt << EOI
Backup Date: $(date)
Backup Location: $BACKUP_DIR
Pre-deployment backup
EOI

echo "✓ Backup completed at: $BACKUP_DIR"
echo ""

# Step 2: Pull Latest Code
echo "▶ Pulling latest code..."
cd /var/www/eventlinez
git fetch origin
git checkout main
git pull origin main
echo "✓ Code updated"
echo ""

# Step 3: Activate Virtual Environment
echo "▶ Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Step 4: Install Dependencies
echo "▶ Installing/updating dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies updated"
echo ""

# Step 5: Collect Static Files
echo "▶ Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

# Step 6: Run Migrations
echo "▶ Running database migrations..."
python manage.py migrate
echo "✓ Migrations applied"
echo ""

# Step 7: Check for any issues
echo "▶ Checking deployment..."
python manage.py check --deploy
echo ""

# Step 8: Restart Services
echo "▶ Restarting services..."
if systemctl is-active --quiet gunicorn; then
    sudo systemctl restart gunicorn
    echo "  ✓ Gunicorn restarted"
else
    echo "  ⚠ Gunicorn service not found"
fi

if systemctl is-active --quiet nginx; then
    sudo systemctl restart nginx
    echo "  ✓ Nginx restarted"
else
    echo "  ⚠ Nginx service not found"
fi
echo ""

echo "╔════════════════════════════════════════╗"
echo "║     Deployment Completed Successfully  ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Please test the application at: https://eventlinez.com.br"
echo ""

ENDSSH

if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Deployment Successful! 🎉       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test the application at https://eventlinez.com.br"
    echo "2. Verify the edit event page works correctly"
    echo "3. Test the free event checkbox functionality"
    echo "4. Check that the datetime picker is working"
    echo "5. Monitor logs for any errors"
    echo ""
    echo "Monitor logs with:"
    echo "  ssh $PROD_USER@$PROD_HOST 'sudo journalctl -u gunicorn -f'"
    echo ""
else
    print_error "Deployment failed!"
    echo ""
    echo "To rollback, SSH to the server and restore from backup:"
    echo "  ssh $PROD_USER@$PROD_HOST"
    echo "  # Check latest backup: ls -la /home/sunset/backups/"
    echo "  # Restore as needed"
fi

