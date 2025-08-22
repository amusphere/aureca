# Deployment Checklist for Stripe Billing Migration

This checklist ensures that all environment variables and configurations are properly set up for each deployment environment.

## Pre-Deployment Checklist

### 1. Environment Configuration ✅

#### Development Environment
- [ ] Copy environment files: `./scripts/setup-environment.sh development`
- [ ] Update `.env` files with actual API keys
- [ ] Verify Stripe test keys are used (`sk_test_*`, `pk_test_*`)
- [ ] Set up local webhook with Stripe CLI: `stripe listen --forward-to localhost:8000/api/stripe/webhook`
- [ ] Test environment validation: `python scripts/validate-environment.py development`

#### Staging Environment
- [ ] Copy environment files: `./scripts/setup-environment.sh staging`
- [ ] Update `.env` files with staging API keys
- [ ] Verify Stripe test keys are used for staging
- [ ] Configure staging webhook endpoint in Stripe Dashboard
- [ ] Update database URL for staging database
- [ ] Test environment validation: `python scripts/validate-environment.py staging`

#### Production Environment
- [ ] Copy environment files: `./scripts/setup-environment.sh production`
- [ ] Update `.env` files with production API keys
- [ ] Verify Stripe live keys are used (`sk_live_*`, `pk_live_*`)
- [ ] Configure production webhook endpoint in Stripe Dashboard
- [ ] Enable webhook signature verification
- [ ] Update database URL for production database
- [ ] Test environment validation: `python scripts/validate-environment.py production`

### 2. Stripe Configuration ✅

#### Stripe Dashboard Setup
- [ ] Create Stripe account (if not exists)
- [ ] Set up products and pricing in Stripe Dashboard
- [ ] Create pricing table and note the ID
- [ ] Configure webhook endpoints for each environment
- [ ] Enable required webhook events:
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`

#### API Keys
- [ ] Development: Test keys configured
- [ ] Staging: Test keys configured (different from dev)
- [ ] Production: Live keys configured
- [ ] Webhook secrets configured for each environment
- [ ] Keys are properly secured and not committed to version control

### 3. Database Migration ✅

- [ ] Run database migrations: `docker compose run --rm backend alembic upgrade head`
- [ ] Verify `users` table has `stripe_customer_id` column
- [ ] Verify `subscriptions` table exists with all required columns
- [ ] Test database connectivity from application

### 4. Application Testing ✅

#### Health Checks
- [ ] Application starts successfully: `docker compose up`
- [ ] Health endpoint responds: `GET /api/health/`
- [ ] Environment validation passes: `GET /api/health/environment`
- [ ] Database connection works
- [ ] Stripe configuration is valid

#### Functional Testing
- [ ] User registration/login works
- [ ] Stripe customer creation works (first subscription access)
- [ ] Subscription purchase flow works
- [ ] Customer portal access works
- [ ] Webhook processing works
- [ ] Premium feature access control works

### 5. Security Verification ✅

- [ ] Webhook signature verification is enabled
- [ ] API keys are environment-specific
- [ ] No sensitive data in logs
- [ ] HTTPS is enabled for staging/production
- [ ] Database connections are secure
- [ ] Environment variables are properly secured

## Deployment Commands

### Development
```bash
# Set up environment
./scripts/setup-environment.sh development

# Start application
docker compose up

# Run migrations
docker compose run --rm backend alembic upgrade head

# Validate configuration
curl http://localhost:8000/api/health/environment
```

### Staging
```bash
# Set up environment
./scripts/setup-environment.sh staging

# Update .env files with staging keys
# Deploy to staging environment
# Run migrations on staging database

# Validate configuration
curl https://api-staging.yourdomain.com/api/health/environment
```

### Production
```bash
# Set up environment
./scripts/setup-environment.sh production

# Update .env files with production keys
# Deploy to production environment
# Run migrations on production database

# Validate configuration
curl https://api.yourdomain.com/api/health/environment
```

## Post-Deployment Verification

### 1. Smoke Tests
- [ ] Application loads successfully
- [ ] User can log in
- [ ] Subscription page loads
- [ ] Health endpoints respond correctly

### 2. Integration Tests
- [ ] Create test subscription (use test card in staging)
- [ ] Verify webhook delivery in Stripe Dashboard
- [ ] Test subscription management in Customer Portal
- [ ] Verify premium features are properly gated

### 3. Monitoring Setup
- [ ] Set up application monitoring
- [ ] Monitor Stripe webhook delivery
- [ ] Set up alerts for failed payments
- [ ] Monitor database performance
- [ ] Set up error tracking

## Rollback Plan

If issues are encountered during deployment:

1. **Immediate Rollback**
   ```bash
   # Revert to previous application version
   git checkout <previous-version>
   docker compose up
   ```

2. **Database Rollback** (if needed)
   ```bash
   # Rollback database migrations
   docker compose run --rm backend alembic downgrade <previous-revision>
   ```

3. **Stripe Configuration**
   - Disable new webhooks in Stripe Dashboard
   - Revert to previous webhook endpoints if needed

## Environment Variables Reference

### Required Frontend Variables
```bash
NEXT_PUBLIC_APP_NAME="Nadeshiko.AI"
API_BASE_URL="https://api.yourdomain.com/api"
FRONTEND_URL="https://yourdomain.com"
NEXT_PUBLIC_AUTH_SYSTEM="clerk"
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_live_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID="prctbl_..."
```

### Required Backend Variables
```bash
APP_NAME="Nadeshiko.AI"
DATABASE_URL="postgresql://user:password@host:5432/database"
FRONTEND_URL="https://yourdomain.com"
CLERK_SECRET_KEY="sk_live_..."
CLERK_WEBHOOK_SECRET="whsec_..."
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
OPENAI_API_KEY="sk-..."
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."
GOOGLE_REDIRECT_URI="https://yourdomain.com/api/auth/google/callback"
GOOGLE_OAUTH_ENCRYPTION_KEY="..."
```

## Support and Troubleshooting

### Common Issues
1. **Webhook signature verification fails**: Check webhook secret and HTTPS configuration
2. **Stripe keys mismatch**: Ensure secret and publishable keys are from same environment
3. **Database connection fails**: Verify database URL and credentials
4. **CORS issues**: Check frontend URL configuration

### Debug Commands
```bash
# Check Stripe configuration
curl -H "Authorization: Bearer $STRIPE_SECRET_KEY" https://api.stripe.com/v1/account

# Test webhook endpoint
curl -X POST https://api.yourdomain.com/api/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{"test": true}'

# Validate environment
python scripts/validate-environment.py production
```

### Getting Help
- Check application logs for detailed error messages
- Review Stripe Dashboard for webhook delivery status
- Consult the environment configuration documentation
- Contact development team for assistance