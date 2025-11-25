# CI/CD Pipeline Setup for Eventlinez

This document explains how to set up and use the automated CI/CD pipeline for the Eventlinez Django application.

## Overview

The CI/CD pipeline consists of three main workflows:

1. **Test Environment Deployment** (`deploy-test.yml`) - Deploys to test server when `develop` branch is updated
2. **Production Deployment** (`deploy-production.yml`) - Deploys to production when `main` branch is updated
3. **Production Rollback** (`rollback.yml`) - Manual rollback workflow for emergency situations

## Prerequisites

### 1. GitHub Repository Secrets

You need to set up the following secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

#### Production Server Secrets:
- `PRODUCTION_SSH_KEY` - Private SSH key for production server access
- `PRODUCTION_HOST` - Production server IP or hostname (e.g., `50.116.31.214`)
- `PRODUCTION_USER` - SSH username for production server (e.g., `sunset`)

#### Test Server Secrets:
- `TEST_SSH_KEY` - Private SSH key for test server access  
- `TEST_HOST` - Test server IP or hostname (e.g., `45.79.112.247`)
- `TEST_USER` - SSH username for test server (e.g., `sunset`)

### 2. SSH Key Generation

Generate SSH keys for GitHub Actions to access your servers:

```bash
# Generate a new SSH key pair
ssh-keygen -t rsa -b 4096 -C "github-actions@eventlinez" -f ~/.ssh/eventlinez_deploy

# Copy the public key to your servers
ssh-copy-id -i ~/.ssh/eventlinez_deploy.pub sunset@your-server-ip

# Add the private key content to GitHub secrets
cat ~/.ssh/eventlinez_deploy  # Copy this content to GitHub secrets
```

### 3. Server Prerequisites

Ensure your servers have:
- Git installed and repository cloned
- Python virtual environment set up
- Required system services (nginx, gunicorn/eventlinez.service)
- Proper file permissions
- Database access (PostgreSQL for production, SQLite for test)

## Workflow Details

### Test Environment Deployment

**Trigger**: Push to `develop` branch or pull request to `develop`

**Process**:
1. Runs automated tests with PostgreSQL
2. Deploys to test server if tests pass
3. Updates dependencies and runs migrations
4. Restarts services and performs health check

**Test URL**: `http://test.eventlinez.com`

### Production Deployment

**Trigger**: Push to `main` branch (manual trigger also available)

**Process**:
1. Runs comprehensive tests
2. Creates automatic backup of current production state
3. Deploys to production server
4. Runs database migrations and collects static files
5. Performs extensive health checks
6. Cleans up old backups (keeps last 10)

**Production URL**: `https://eventlinez.com`

### Rollback Workflow

**Trigger**: Manual execution only (workflow_dispatch)

**Requirements**: 
- Must type "CONFIRM" in the confirmation field
- Optionally specify backup timestamp

**Process**:
1. Creates pre-rollback backup
2. Restores database, media files, and environment from backup
3. Reverts code to previous commit (if backup info available)
4. Restarts services and verifies functionality

## Usage Guide

### Normal Development Workflow

1. **Feature Development**:
   ```bash
   # Work on develop branch
   git checkout develop
   git pull origin develop
   
   # Create feature branch
   git checkout -b feature/your-feature
   # ... make changes ...
   git commit -m "Add new feature"
   git push origin feature/your-feature
   ```

2. **Testing**:
   ```bash
   # Create pull request to develop branch
   # This triggers test environment deployment
   # Test your changes at http://test.eventlinez.com
   ```

3. **Production Release**:
   ```bash
   # Merge to main branch (triggers production deployment)
   git checkout main
   git merge develop
   git push origin main
   ```

### Emergency Rollback

1. Go to GitHub Actions tab in your repository
2. Select "Rollback Production" workflow
3. Click "Run workflow"
4. Enter "CONFIRM" in the confirmation field
5. Optionally specify a backup timestamp (format: YYYYMMDD_HHMMSS)
6. Click "Run workflow" button

### Monitoring Deployments

#### Check Deployment Status:
- Visit GitHub Actions tab to see workflow progress
- Each step shows detailed logs and status

#### Server Logs:
```bash
# Production server logs
ssh sunset@50.116.31.214
sudo journalctl -u gunicorn -f  # Follow gunicorn logs
sudo journalctl -u nginx -f     # Follow nginx logs

# Test server logs  
ssh sunset@45.79.112.247
sudo journalctl -u eventlinez.service -f
```

#### Health Checks:
```bash
# Check if services are running
systemctl status gunicorn
systemctl status nginx

# Test application response
curl -I http://localhost/
curl -I https://eventlinez.com/
```

## Backup Management

### Automatic Backups
- Created before every production deployment
- Stored in `/home/sunset/backups/` with timestamp
- Old backups automatically cleaned (keeps last 10)

### Manual Backup
```bash
# On production server
sudo -u postgres pg_dump eventlinez_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### List Available Backups
```bash
# On production server
ls -la /home/sunset/backups/
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**:
   - Verify SSH keys are correctly added to GitHub secrets
   - Check server SSH access manually
   - Ensure correct server IP/hostname in secrets

2. **Database Migration Errors**:
   - Check database connectivity
   - Verify database user permissions
   - Review migration files for conflicts

3. **Static Files Issues**:
   - Verify STATIC_ROOT setting in Django settings
   - Check file permissions on staticfiles directory
   - Ensure nginx configuration serves static files correctly

4. **Service Start Failures**:
   - Check systemd service files
   - Verify virtual environment paths
   - Review application logs for errors

### Rollback Scenarios

- **Use automatic rollback**: When deployment completes but application has issues
- **Use manual rollback**: When you need to restore to a specific point in time
- **Emergency procedure**: Always creates pre-rollback backup for safety

## Security Considerations

1. **SSH Keys**: Use dedicated keys for CI/CD, rotate regularly
2. **Secrets**: Never commit secrets to repository
3. **Permissions**: Ensure proper file permissions on servers
4. **Backups**: Secure backup storage and access

## Notifications

You can extend the workflows to send notifications:

- Slack/Discord webhooks for deployment status
- Email notifications for failures
- Custom monitoring integrations

## Maintenance

### Regular Tasks:
- Monitor backup disk usage
- Review and clean old backups manually if needed
- Update dependencies in requirements.txt
- Review and update GitHub Actions versions

### Monthly Tasks:
- Test rollback procedure
- Verify backup integrity
- Review deployment logs
- Update documentation as needed

## Support

For issues with the CI/CD pipeline:
1. Check GitHub Actions logs first
2. Verify server status and logs
3. Test manual deployment scripts
4. Review this documentation for troubleshooting steps

---

**Note**: Always test changes on the test environment before deploying to production. The CI/CD pipeline includes safety checks, but manual verification is recommended for critical changes.