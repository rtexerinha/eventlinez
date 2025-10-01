# Environment Setup for Eventlinez

## Required Environment Variables

To run the application locally, you need to set up the following environment variables:

### 1. SendGrid Configuration
```bash
export SENDGRID_API_KEY="your_sendgrid_api_key_here"
```

### 2. Stripe Configuration
```bash
export STRIPE_PUBLISHABLE_KEY="your_stripe_publishable_key_here"
export STRIPE_SECRET_KEY="your_stripe_secret_key_here"
```

## Quick Setup for Local Development

### Option 1: Using docker-compose.local.yml (Recommended)
1. Copy `docker-compose.local.yml` and update it with your actual keys
2. Run: `docker-compose -f docker-compose.yml -f docker-compose.local.yml up`

### Option 2: Using Environment Variables
1. Set the environment variables in your shell:
   ```bash
   export SENDGRID_API_KEY="SG.your_actual_key_here"
   export STRIPE_PUBLISHABLE_KEY="pk_test_your_actual_key_here"
   export STRIPE_SECRET_KEY="sk_test_your_actual_key_here"
   ```
2. Run: `docker-compose up`

## Security Notes

- Never commit real API keys to the repository
- Use environment variables or local override files
- The `docker-compose.local.yml` file is gitignored for security
- Always use test keys for development

## Production Deployment

For production, set these environment variables in your deployment platform:
- Heroku: Use `heroku config:set`
- AWS: Use Parameter Store or Secrets Manager
- Docker: Use environment files or secrets
