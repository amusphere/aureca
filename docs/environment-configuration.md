# Environment Configuration Guide

This document outlines the environment variable configuration for the Stripe billing migration, including setup for development, staging, and production environments.

## Environment Variables Overview

### Frontend Environment Variables

#### Required Stripe Variables
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: Stripe publishable key (starts with `pk_`)
- `NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID`: Stripe pricing table ID (starts with `prctbl_`)

#### Other Required Variables
- `NEXT_PUBLIC_APP_NAME`: Application name
- `API_BASE_URL`: Backend API URL
- `FRONTEND_URL`: Frontend application URL
- `NEXT_PUBLIC_AUTH_SYSTEM`: Authentication system ("clerk" or "email_password")
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk publishable key (if using Clerk)
- `CLERK_SECRET_KEY`: Clerk secret key (if using Clerk)

### Backend Environment Variables

#### Required Stripe Variables
- `STRIPE_SECRET_KEY`: Stripe secret key (starts with `sk_`)
- `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key (starts with `pk_`)
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook endpoint secret (starts with `whsec_`)

#### Optional Stripe Variables
- `STRIPE_API_VERSION`: Stripe API version (default: "2023-10-16")
- `STRIPE_WEBHOOK_TOLERANCE`: Webhook timestamp tolerance in seconds (default: 300)

#### Other Required Variables
- `APP_NAME`: Application name
- `DATABASE_URL`: PostgreSQL database connection string
- `FRONTEND_URL`: Frontend application URL
- `CLERK_SECRET_KEY`: Clerk secret key
- `CLERK_WEBHOOK_SECRET`: Clerk webhook secret
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: Google OAuth redirect URI
- `GOOGLE_OAUTH_ENCRYPTION_KEY`: Encryption key for Google OAuth tokens

## Environment-Specific Configuration

### Development Environment

#### Stripe Configuration
- Use Stripe **test mode** keys (keys starting with `sk_test_` and `pk_test_`)
- Set up test webhooks pointing to your local development server
- Use Stripe CLI for local webhook testing: `stripe listen --forward-to localhost:8000/api/stripe/webhook`

#### Example Development Configuration

**Frontend (.env)**
```bash
NEXT_PUBLIC_APP_NAME="Nadeshiko.AI (Dev)"
API_BASE_URL="http://backend:8000/api"
FRONTEND_URL="http://localhost:3000"
NEXT_PUBLIC_AUTH_SYSTEM="clerk"
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."

# Stripe Test Mode
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."
NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID="prctbl_..."
```

**Backend (.env)**
```bash
APP_NAME="Nadeshiko.AI (Dev)"
DATABASE_URL="postgresql://postgres:password@db:5432/development"
FRONTEND_URL="http://localhost:3000"

# Clerk
CLERK_SECRET_KEY="sk_test_..."
CLERK_WEBHOOK_SECRET="whsec_..."

# Stripe Test Mode
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# Other services...
OPENAI_API_KEY="sk-..."
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."
GOOGLE_REDIRECT_URI="http://localhost:3000/api/auth/google/callback"
GOOGLE_OAUTH_ENCRYPTION_KEY="..."
```

### Staging Environment

#### Stripe Configuration
- Use Stripe **test mode** keys for staging
- Set up staging webhooks pointing to your staging server
- Test all payment flows thoroughly before production

#### Example Staging Configuration

**Frontend**
```bash
NEXT_PUBLIC_APP_NAME="Nadeshiko.AI (Staging)"
API_BASE_URL="https://api-staging.yourdomain.com/api"
FRONTEND_URL="https://staging.yourdomain.com"
NEXT_PUBLIC_AUTH_SYSTEM="clerk"
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
CLERK_SECRET_KEY="sk_test_..."

# Stripe Test Mode (same as dev but different webhook endpoints)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."
NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID="prctbl_..."
```

**Backend**
```bash
APP_NAME="Nadeshiko.AI (Staging)"
DATABASE_URL="postgresql://user:password@staging-db:5432/staging"
FRONTEND_URL="https://staging.yourdomain.com"

# Clerk
CLERK_SECRET_KEY="sk_test_..."
CLERK_WEBHOOK_SECRET="whsec_..."

# Stripe Test Mode
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_staging_webhook_secret"

# Other services with staging configurations...
```

### Production Environment

#### Stripe Configuration
- Use Stripe **live mode** keys (keys starting with `sk_live_` and `pk_live_`)
- Set up production webhooks with proper SSL certificates
- Enable webhook signature verification
- Monitor webhook delivery and retry failed webhooks

#### Example Production Configuration

**Frontend**
```bash
NEXT_PUBLIC_APP_NAME="Nadeshiko.AI"
API_BASE_URL="https://api.yourdomain.com/api"
FRONTEND_URL="https://yourdomain.com"
NEXT_PUBLIC_AUTH_SYSTEM="clerk"
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_live_..."
CLERK_SECRET_KEY="sk_live_..."

# Stripe Live Mode
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID="prctbl_live_..."
```

**Backend**
```bash
APP_NAME="Nadeshiko.AI"
DATABASE_URL="postgresql://user:password@prod-db:5432/production"
FRONTEND_URL="https://yourdomain.com"

# Clerk
CLERK_SECRET_KEY="sk_live_..."
CLERK_WEBHOOK_SECRET="whsec_live_..."

# Stripe Live Mode
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_live_webhook_secret"

# Other services with production configurations...
```

## Security Best Practices

### Environment Variable Security
1. **Never commit actual keys to version control**
2. **Use different keys for each environment**
3. **Rotate keys regularly**
4. **Use environment-specific webhook secrets**
5. **Enable webhook signature verification**

### Stripe-Specific Security
1. **Use test mode for development and staging**
2. **Verify webhook signatures on all environments**
3. **Set appropriate webhook tolerance (default: 300 seconds)**
4. **Monitor failed webhook deliveries**
5. **Use HTTPS for all webhook endpoints in staging/production**

## Webhook Configuration

### Development
- Use Stripe CLI: `stripe listen --forward-to localhost:8000/api/stripe/webhook`
- Webhook URL: `http://localhost:8000/api/stripe/webhook`

### Staging
- Webhook URL: `https://api-staging.yourdomain.com/api/stripe/webhook`
- Enable events: `customer.subscription.*`, `invoice.payment_*`

### Production
- Webhook URL: `https://api.yourdomain.com/api/stripe/webhook`
- Enable events: `customer.subscription.*`, `invoice.payment_*`
- Enable webhook signature verification
- Set up monitoring and alerting for failed webhooks

## Validation and Testing

### Environment Validation
The application includes built-in validation for Stripe configuration:

```python
# Backend validation
from app.config.stripe import StripeConfig

# Check if Stripe is properly configured
if not StripeConfig.is_configured():
    raise ValueError("Stripe configuration is incomplete")

# Check if in test mode
if StripeConfig.is_test_mode():
    print("Running in Stripe test mode")
```

### Testing Checklist
- [ ] All required environment variables are set
- [ ] Stripe keys match the environment (test vs live)
- [ ] Webhook endpoints are accessible
- [ ] Webhook signature verification works
- [ ] Payment flows work end-to-end
- [ ] Subscription management works
- [ ] Error handling works properly

## Deployment Considerations

### Docker Compose
Update your `docker-compose.yml` to include environment variables:

```yaml
services:
  backend:
    environment:
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}

  frontend:
    environment:
      - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY}
      - NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID=${NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID}
```

### CI/CD Pipeline
1. Set environment variables in your CI/CD platform
2. Use different variable sets for different environments
3. Validate configuration before deployment
4. Test webhook connectivity after deployment

## Troubleshooting

### Common Issues
1. **Webhook signature verification fails**: Check webhook secret and ensure HTTPS in production
2. **Payment flows don't work**: Verify publishable key matches secret key environment
3. **Subscription status not updating**: Check webhook delivery and processing
4. **CORS issues**: Ensure frontend URL is correctly configured

### Debug Commands
```bash
# Check Stripe configuration
curl -H "Authorization: Bearer $STRIPE_SECRET_KEY" https://api.stripe.com/v1/account

# Test webhook endpoint
curl -X POST http://localhost:8000/api/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```