# 🚀 Eventlinez CI/CD Deployment Guide

This guide explains how to set up continuous integration and deployment for the Eventlinez application to your test server.

## 📋 Prerequisites

- GitHub repository with admin access
- Test server: `45.79.112.247` (test.eventlinez.com)
- Server access: User `sunset`, Password: `Texera123@`
- Domain configured to point to the server

## 🔧 Server Setup

### 1. Initial Server Configuration

Connect to your server and install required packages:

```bash
ssh sunset@45.79.112.247
# Enter password: Texera123@

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-venv python3-pip git nginx curl
sudo apt install -y postgresql postgresql-contrib  # Optional: if using PostgreSQL

# Install Docker (optional, for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker sunset
```

### 2. Set up SSH Key for GitHub Actions

On your server, generate an SSH key for GitHub Actions deployment:

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez.com" -f ~/.ssh/github_actions_key

# Display the public key (copy this for GitHub)
cat ~/.ssh/github_actions_key.pub

# Display the private key (copy this for GitHub Secrets)
cat ~/.ssh/github_actions_key
```

### 3. Prepare Application Directory

```bash
# Create application directory
sudo mkdir -p /home/sunset/eventlinez
sudo chown sunset:sunset /home/sunset/eventlinez

# Create backup directory
mkdir -p /home/sunset/backups

# Clone the repository (initial setup)
cd /home/sunset
git clone https://github.com/your-username/eventlinez.git
cd eventlinez
git checkout develop
```

## 🔐 GitHub Configuration

### 1. Add Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `TEST_SERVER_HOST` | `45.79.112.247` | Test server IP address |
| `TEST_SERVER_USER` | `sunset` | SSH username |
| `TEST_SERVER_SSH_KEY` | `[Private SSH Key]` | Private key from server (entire content) |
| `DEPLOY_PATH` | `/home/sunset` | Base deployment path |

### 2. SSH Key Configuration

1. **Add Public Key to Server**: 
   ```bash
   # On server, add the public key to authorized_keys
   echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

2. **Add Private Key to GitHub Secrets**:
   - Copy the entire private key (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)
   - Paste it as the value for `TEST_SERVER_SSH_KEY` secret

## 🔄 Workflow Explained

### Trigger Events
- **Push to `develop`**: Automatically deploys to test server
- **Pull Request to `develop`**: Runs tests only

### Pipeline Stages

1. **🧪 Testing Stage**:
   - Sets up Python environment
   - Installs dependencies
   - Runs Django tests
   - Performs code linting
   - Security scanning

2. **🚀 Deployment Stage** (only on push to develop):
   - Connects to test server via SSH
   - Creates backup of current deployment
   - Pulls latest code from develop branch
   - Updates dependencies
   - Runs database migrations
   - Collects static files
   - Restarts services
   - Performs health checks

3. **🔍 Security Stage**:
   - Runs security vulnerability scans
   - Checks for known security issues in dependencies

## 📂 Server Directory Structure

```
/home/sunset/
├── eventlinez/                 # Main application
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                   # Environment variables
│   ├── venv/                  # Virtual environment
│   ├── staticfiles/           # Collected static files
│   └── media/                 # User uploaded files
├── backups/                   # Automatic backups
│   ├── eventlinez_backup_20240315_140230/
│   └── eventlinez_backup_20240315_120115/
└── logs/
    └── eventlinez-deploy.log  # Deployment logs
```

## 🔧 Manual Deployment

If you need to deploy manually, you can run the deployment script:

```bash
# On the server
cd /home/sunset/eventlinez
./deploy.sh
```

## 🐳 Docker Deployment (Alternative)

If you prefer Docker deployment, you can modify the workflow to use Docker:

1. **Update docker-compose.yml** for production:
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DEBUG=False
         - ALLOWED_HOSTS=test.eventlinez.com,45.79.112.247
       volumes:
         - ./staticfiles:/app/staticfiles
         - ./media:/app/media
   ```

2. **Modify the GitHub Actions workflow** to use Docker commands instead of systemd.

## 🌐 Nginx Configuration

The deployment script automatically creates Nginx configuration at `/etc/nginx/sites-available/eventlinez`:

```nginx
server {
    listen 80;
    server_name test.eventlinez.com 45.79.112.247;

    location /static/ {
        alias /home/sunset/eventlinez/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/sunset/eventlinez/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

## 🔍 Monitoring and Logs

### Application Logs
```bash
# View application logs
sudo journalctl -u eventlinez.service -f

# View deployment logs
tail -f /var/log/eventlinez-deploy.log

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks
```bash
# Check if application is running
curl http://localhost:8000/admin/

# Check service status
sudo systemctl status eventlinez.service
sudo systemctl status nginx
```

## 🚨 Troubleshooting

### Common Issues

1. **SSH Connection Failed**:
   - Verify SSH key is correctly added to GitHub Secrets
   - Ensure public key is in `~/.ssh/authorized_keys` on server
   - Check server firewall settings

2. **Permission Denied**:
   - Ensure `sunset` user owns the deployment directory
   - Check file permissions: `chmod -R 755 /home/sunset/eventlinez`

3. **Application Not Starting**:
   - Check application logs: `sudo journalctl -u eventlinez.service`
   - Verify environment variables in `.env` file
   - Ensure database is accessible

4. **Static Files Not Loading**:
   - Run: `python manage.py collectstatic --noinput`
   - Check Nginx configuration and reload: `sudo nginx -t && sudo systemctl reload nginx`

### Manual Recovery

If deployment fails, you can restore from backup:
```bash
cd /home/sunset/backups
# List available backups
ls -la eventlinez_backup_*

# Restore from backup (replace with actual backup name)
sudo systemctl stop eventlinez.service
rm -rf /home/sunset/eventlinez
cp -r eventlinez_backup_YYYYMMDD_HHMMSS /home/sunset/eventlinez
sudo systemctl start eventlinez.service
```

## 🔐 Security Considerations

1. **Environment Variables**: Store sensitive data in `.env` file (never commit to git)
2. **SSH Keys**: Use separate SSH keys for deployment (don't reuse personal keys)
3. **Server Access**: Regularly update server packages and security patches
4. **Database**: Use strong passwords and consider PostgreSQL for production
5. **HTTPS**: Consider setting up SSL certificate (Let's Encrypt) for production

## 📞 Support

If you encounter issues:
1. Check GitHub Actions logs in the repository
2. Review server logs using the commands above
3. Verify all secrets are correctly configured in GitHub
4. Ensure server has sufficient resources (disk space, memory)

---

**🎉 Once everything is set up, every push to the `develop` branch will automatically deploy to test.eventlinez.com!**
