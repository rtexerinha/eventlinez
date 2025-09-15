# 🔑 SSH Key Setup Guide for GitHub Actions

## Step-by-Step Instructions

### 1. Connect to Your Test Server

```bash
ssh sunset@45.79.112.247
# Enter password: Texera123@
```

### 2. Generate SSH Key Pair

Once connected to your server, run these commands:

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh

# Generate a new SSH key pair specifically for GitHub Actions
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key

# When prompted:
# - "Enter passphrase": Just press ENTER (leave empty for automation)
# - "Enter same passphrase again": Press ENTER again
```

### 3. Set Proper Permissions

```bash
# Set correct permissions for SSH files
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_actions_key
chmod 644 ~/.ssh/github_actions_key.pub
```

### 4. Add Public Key to Authorized Keys

```bash
# Add the public key to authorized_keys so GitHub Actions can connect
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys

# Set proper permissions for authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 5. Get the Private Key for GitHub Secrets

```bash
# Display the PRIVATE key (this is what goes in GitHub Secrets)
cat ~/.ssh/github_actions_key
```

**Important:** Copy the ENTIRE output including the header and footer lines:
```
-----BEGIN OPENSSH PRIVATE KEY-----
[... key content ...]
-----END OPENSSH PRIVATE KEY-----
```

### 6. Get the Public Key (for reference)

```bash
# Display the PUBLIC key (for your records)
cat ~/.ssh/github_actions_key.pub
```

## 📋 Using the Keys in GitHub

### Add to GitHub Repository Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Create secret:
   - **Name**: `TEST_SERVER_SSH_KEY`
   - **Value**: Paste the ENTIRE private key content (from step 5 above)

## 🧪 Test the SSH Connection

To verify everything works, you can test the SSH connection:

```bash
# From your local machine or another server, test the connection
ssh -i ~/.ssh/github_actions_key sunset@45.79.112.247

# If successful, you should connect without entering a password
```

## 🔒 Security Best Practices

1. **Never share the private key** - Only add it to GitHub Secrets
2. **Keep the public key safe** - You can share this freely
3. **Use a separate key** - Don't reuse your personal SSH keys
4. **No passphrase** - GitHub Actions needs passwordless access for automation

## 🐛 Troubleshooting

### Permission Denied Error
```bash
# If you get permission errors, fix permissions:
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_actions_key
chmod 600 ~/.ssh/authorized_keys
```

### Key Not Working
```bash
# Verify the key was added correctly:
grep "github-actions@eventlinez.com" ~/.ssh/authorized_keys

# Check SSH service status:
sudo systemctl status ssh
```

### Connection Refused
```bash
# Check if SSH service is running:
sudo systemctl start ssh
sudo systemctl enable ssh

# Check firewall:
sudo ufw allow ssh
```

## 📝 Complete Example

Here's what the complete process looks like:

```bash
# Connect to server
ssh sunset@45.79.112.247

# Generate key
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key
# Press ENTER twice (no passphrase)

# Set permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_actions_key
chmod 644 ~/.ssh/github_actions_key.pub

# Add to authorized keys
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Copy this output to GitHub Secrets as TEST_SERVER_SSH_KEY:
cat ~/.ssh/github_actions_key
```

## ✅ Verification Checklist

- [ ] SSH key pair generated
- [ ] Permissions set correctly (700, 600, 644)
- [ ] Public key added to authorized_keys
- [ ] Private key copied to GitHub Secrets
- [ ] Test connection works
- [ ] GitHub Actions workflow can deploy

Once you complete these steps, your GitHub Actions workflow will be able to automatically deploy to your test server! 🚀
