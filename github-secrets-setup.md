# 🔐 GitHub Secrets Setup Guide

## Required GitHub Repository Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 🔑 Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `TEST_SERVER_HOST` | `45.79.112.247` | IP address of your test server |
| `TEST_SERVER_USER` | `sunset` | SSH username for deployment |
| `TEST_SERVER_SSH_KEY` | `[Private SSH Key]` | SSH private key for server access |
| `DEPLOY_PATH` | `/home/sunset` | Base deployment directory on server |

## 🚀 Step-by-Step Setup

### 1. Get SSH Keys from Server

After running the server setup script, you'll get SSH keys. Copy them:

```bash
# On your test server (45.79.112.247)
ssh sunset@45.79.112.247

# Display public key (for reference)
cat ~/.ssh/github_actions_key.pub

# Display private key (copy this entire output)
cat ~/.ssh/github_actions_key
```

### 2. Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

#### TEST_SERVER_HOST
```
Name: TEST_SERVER_HOST
Value: 45.79.112.247
```

#### TEST_SERVER_USER
```
Name: TEST_SERVER_USER
Value: sunset
```

#### TEST_SERVER_SSH_KEY
```
Name: TEST_SERVER_SSH_KEY
Value: -----BEGIN OPENSSH PRIVATE KEY-----
[paste the entire private key content here]
-----END OPENSSH PRIVATE KEY-----
```

#### DEPLOY_PATH
```
Name: DEPLOY_PATH
Value: /home/sunset
```

## ✅ Verification

After setting up the secrets, you can verify by:

1. **Push to develop branch** - this will trigger the deployment
2. **Check Actions tab** in your GitHub repository
3. **Monitor the deployment** logs in the Actions workflow
4. **Visit your site** at http://test.eventlinez.com

## 🔧 Troubleshooting

### SSH Connection Issues
- Ensure the private key is copied completely (including header/footer)
- Verify the public key is in `~/.ssh/authorized_keys` on the server
- Check that the SSH key permissions are correct (600)

### Deployment Failures
- Check the Actions log in GitHub for detailed error messages
- Verify all secrets are correctly named and contain the right values
- Ensure the server has sufficient disk space and memory

### Server Access Issues
- Test SSH connection manually: `ssh -i ~/.ssh/github_actions_key sunset@45.79.112.247`
- Verify firewall allows SSH connections
- Check that the user `sunset` has proper permissions

## 🎯 Quick Test

To quickly test if everything is working:

```bash
# Make a small change to your code
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: trigger deployment"
git push origin develop
```

Then watch the Actions tab in GitHub to see the deployment in progress!
