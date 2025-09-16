# Direct SSH Setup Commands

Since the download is failing, here are the direct commands to run on your test server (45.79.112.247):

## 🔑 Step-by-Step SSH Setup on Test Server

```bash
# 1. Create SSH directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 2. Generate SSH key pair for GitHub Actions
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key -N ""

# 3. Add public key to authorized_keys
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 4. Display the private key (copy this to GitHub secrets)
echo "🔐 PRIVATE KEY FOR GITHUB SECRETS:"
echo "=================================="
cat ~/.ssh/github_actions_key
echo "=================================="

# 5. Set up application directory
APP_DIR="/home/sunset/eventlinez"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# 6. Clone repository if needed
if [ ! -d ".git" ]; then
    git clone https://github.com/rtexerinha/eventlinez.git .
    git checkout develop
else
    git fetch origin
    git checkout develop
    git reset --hard origin/develop
fi

# 7. Set permissions
sudo chown -R sunset:sunset "$APP_DIR"

# 8. Install Docker if not installed
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker sunset
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 9. Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Setup complete! Copy the private key above to GitHub secrets."
```

## 📋 GitHub Secrets to Add

After running the commands above, add these secrets to your GitHub repository:

1. Go to: https://github.com/rtexerinha/eventlinez/settings/secrets/actions
2. Add these 4 secrets:

| Secret Name | Value |
|-------------|--------|
| `TEST_SERVER_SSH_KEY` | [The private key output from step 4 above] |
| `TEST_SERVER_HOST` | `45.79.112.247` |
| `TEST_SERVER_USER` | `sunset` |
| `DEPLOY_PATH` | `/home/sunset/eventlinez` |

## 🧪 Test Deployment

After adding secrets, test with:

```bash
# From your local machine
git commit --allow-empty -m "test: trigger deployment"
git push origin develop
```

The CI/CD pipeline will now deploy automatically! 🚀
