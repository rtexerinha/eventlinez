# GitHub Secrets Setup for CI/CD Deployment

## 🔑 Quick Setup Guide

### Step 1: Run SSH Setup on Test Server

Connect to your test server and run the setup script:

```bash
# Connect to test server
ssh sunset@45.79.112.247

# Download and run the setup script
curl -o setup-ssh-deployment.sh https://raw.githubusercontent.com/rtexerinha/eventlinez/develop/setup-ssh-deployment.sh
chmod +x setup-ssh-deployment.sh
./setup-ssh-deployment.sh
```

### Step 2: Configure GitHub Secrets

1. **Go to your repository**: https://github.com/rtexerinha/eventlinez
2. **Navigate to**: Settings → Secrets and variables → Actions
3. **Click**: "New repository secret"
4. **Add these 4 secrets**:

| Secret Name | Value | Description |
|-------------|--------|-------------|
| `TEST_SERVER_SSH_KEY` | [Private key from setup script] | SSH private key for authentication |
| `TEST_SERVER_HOST` | `45.79.112.247` | Test server IP address |
| `TEST_SERVER_USER` | `sunset` | SSH username |
| `DEPLOY_PATH` | `/home/sunset/eventlinez` | Application directory path |

### Step 3: Test Deployment

After adding the secrets, push any change to the `develop` branch:

```bash
git add .
git commit -m "test: trigger deployment"
git push origin develop
```

## 🎯 Expected Results

### Before Setup (Current):
```
🔑 SSH secrets not configured. Skipping deployment.
📋 To enable automatic deployment, add these secrets...
```

### After Setup:
```
✅ SSH secrets configured. Proceeding with deployment.
🚀 Starting deployment to test server...
✅ Deployment to test.eventlinez.com completed successfully!
```

## 🔧 Troubleshooting

### Common Issues:

1. **"Permission denied" error**
   - Ensure the private key is copied exactly (including `-----BEGIN` and `-----END` lines)
   - Check that the public key was added to `~/.ssh/authorized_keys`

2. **"Host key verification failed"**
   - The workflow uses `StrictHostKeyChecking=no` to handle this automatically

3. **"Connection refused"**
   - Verify the server IP (45.79.112.247) is correct
   - Ensure SSH service is running on the server

### Manual SSH Test:

To test SSH connection manually:

```bash
# Test from your local machine (after copying private key to ~/.ssh/test_key)
ssh -i ~/.ssh/test_key -o StrictHostKeyChecking=no sunset@45.79.112.247
```

## 🚀 Deployment Flow

Once configured, every push to `develop` will:

1. ✅ Run tests (PostgreSQL + Django)
2. ✅ Run security scans (safety + bandit)
3. ✅ Connect to test server via SSH
4. ✅ Pull latest code
5. ✅ Run migrations
6. ✅ Collect static files
7. ✅ Restart Docker services
8. ✅ Perform health check
9. ✅ Report deployment status

**🎉 Fully automated deployment to test.eventlinez.com!**
