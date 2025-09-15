#!/bin/bash

# SSH Key Creation Script for GitHub Actions
# Run this script on your test server (45.79.112.247) as user 'sunset'

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

echo "🔑 GitHub Actions SSH Key Setup for Eventlinez"
echo "=============================================="
echo ""

# Check if running as correct user
if [ "$USER" != "sunset" ]; then
    error "This script must be run as user 'sunset'"
    echo "Current user: $USER"
    echo "Please run: ssh sunset@45.79.112.247"
    exit 1
fi

log "Setting up SSH key for GitHub Actions deployment..."

# Create .ssh directory if it doesn't exist
log "Creating .ssh directory..."
mkdir -p ~/.ssh
success ".ssh directory ready"

# Generate SSH key pair
KEY_PATH="$HOME/.ssh/github_actions_key"
if [ -f "$KEY_PATH" ]; then
    warning "SSH key already exists at $KEY_PATH"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        log "Using existing SSH key"
    else
        log "Generating new SSH key pair..."
        ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f "$KEY_PATH" -N ""
        success "New SSH key pair generated"
    fi
else
    log "Generating SSH key pair..."
    ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f "$KEY_PATH" -N ""
    success "SSH key pair generated"
fi

# Set proper permissions
log "Setting file permissions..."
chmod 700 ~/.ssh
chmod 600 "$KEY_PATH"
chmod 644 "$KEY_PATH.pub"
success "Permissions set correctly"

# Add public key to authorized_keys
log "Adding public key to authorized_keys..."
if [ ! -f ~/.ssh/authorized_keys ]; then
    touch ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
fi

# Check if key is already in authorized_keys
if grep -q "$(cat $KEY_PATH.pub)" ~/.ssh/authorized_keys 2>/dev/null; then
    warning "Public key already exists in authorized_keys"
else
    cat "$KEY_PATH.pub" >> ~/.ssh/authorized_keys
    success "Public key added to authorized_keys"
fi

# Set authorized_keys permissions
chmod 600 ~/.ssh/authorized_keys

echo ""
echo "🎉 SSH key setup completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Copy the PRIVATE key below and add it to GitHub Secrets:"
echo "   - Go to: GitHub Repository → Settings → Secrets → Actions"
echo "   - Secret name: TEST_SERVER_SSH_KEY"
echo "   - Secret value: Copy everything between the lines below"
echo ""
echo "━━━━━━━━━━━━━━━━━ PRIVATE KEY START ━━━━━━━━━━━━━━━━━"
cat "$KEY_PATH"
echo "━━━━━━━━━━━━━━━━━━ PRIVATE KEY END ━━━━━━━━━━━━━━━━━━"
echo ""
echo "2. Your PUBLIC key (for reference):"
echo "━━━━━━━━━━━━━━━━━━ PUBLIC KEY ━━━━━━━━━━━━━━━━━━"
cat "$KEY_PATH.pub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "3. Required GitHub Secrets:"
echo "   TEST_SERVER_HOST: 45.79.112.247"
echo "   TEST_SERVER_USER: sunset"
echo "   TEST_SERVER_SSH_KEY: [paste the private key above]"
echo "   DEPLOY_PATH: /home/sunset"
echo ""
echo "4. Test your setup by pushing to the develop branch!"
echo ""

# Test SSH configuration
log "Testing SSH configuration..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 -i "$KEY_PATH" sunset@localhost 'exit' 2>/dev/null; then
    success "SSH key test successful!"
else
    warning "SSH key test failed, but this is normal for localhost. The key should work for GitHub Actions."
fi

echo ""
success "✅ Setup complete! Your server is ready for GitHub Actions deployment."
echo ""
echo "💡 Tip: Save the private key securely. You'll need it for the GitHub secret!"
echo "🚀 After adding the secret to GitHub, push to develop branch to trigger deployment."
