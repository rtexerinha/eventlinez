#!/bin/bash

# SSH Setup Script for GitHub Actions Deployment
# This script should be run on the test server (45.79.112.247)

echo "🔑 Setting up SSH keys for GitHub Actions deployment..."
echo "======================================================="

# Step 1: Create SSH directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Step 2: Generate SSH key pair specifically for GitHub Actions
echo "📋 Generating SSH key pair for GitHub Actions..."
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key -N ""

echo "✅ SSH key pair generated!"

# Step 3: Add public key to authorized_keys
echo "📋 Adding public key to authorized_keys..."
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

echo "✅ Public key added to authorized_keys!"

# Step 4: Display the private key to copy to GitHub
echo ""
echo "🔐 PRIVATE KEY FOR GITHUB SECRETS:"
echo "=================================="
echo "Copy the following private key and add it to your GitHub repository secrets"
echo "as 'TEST_SERVER_SSH_KEY':"
echo ""
cat ~/.ssh/github_actions_key
echo ""
echo "=================================="

# Step 5: Create application directory if it doesn't exist
APP_DIR="/home/sunset/eventlinez"
echo "📁 Setting up application directory: $APP_DIR"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Step 6: Clone repository if it doesn't exist
if [ ! -d ".git" ]; then
    echo "📦 Cloning repository..."
    git clone https://github.com/rtexerinha/eventlinez.git .
    git checkout develop
else
    echo "📦 Repository already exists, pulling latest changes..."
    git fetch origin
    git checkout develop
    git reset --hard origin/develop
fi

# Step 7: Set proper permissions
sudo chown -R sunset:sunset "$APP_DIR"
chmod +x "$APP_DIR/deploy.sh" 2>/dev/null || echo "deploy.sh will be available after next push"

# Step 8: Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker sunset
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "✅ Docker installed!"
else
    echo "✅ Docker already installed!"
fi

# Step 9: Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed!"
else
    echo "✅ Docker Compose already installed!"
fi

echo ""
echo "🎉 SSH Setup Complete!"
echo "======================"
echo ""
echo "📋 Next Steps:"
echo "1. Copy the private key shown above"
echo "2. Go to your GitHub repository: https://github.com/rtexerinha/eventlinez"
echo "3. Navigate to: Settings → Secrets and variables → Actions"
echo "4. Add the following secrets:"
echo "   - Name: TEST_SERVER_SSH_KEY"
echo "     Value: [paste the private key from above]"
echo "   - Name: TEST_SERVER_HOST"
echo "     Value: 45.79.112.247"
echo "   - Name: TEST_SERVER_USER"
echo "     Value: sunset"
echo "   - Name: DEPLOY_PATH"
echo "     Value: /home/sunset/eventlinez"
echo ""
echo "5. Test the deployment by pushing to develop branch"
echo ""
echo "✅ Your CI/CD deployment will now work automatically!"
