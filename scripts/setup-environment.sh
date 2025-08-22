#!/bin/bash

# Environment setup script for Stripe billing migration
# This script helps set up environment variables for different deployment environments

set -e

ENVIRONMENT=${1:-development}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up environment for: $ENVIRONMENT"

# Validate environment parameter
case $ENVIRONMENT in
    development|staging|production)
        echo "✅ Valid environment: $ENVIRONMENT"
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "Usage: $0 <environment>"
        echo "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Function to copy environment files
copy_env_files() {
    local env=$1

    echo "📁 Setting up environment files for $env..."

    # Backend environment file
    if [ -f "$PROJECT_ROOT/backend/.env.$env" ]; then
        echo "  Copying backend/.env.$env to backend/.env"
        cp "$PROJECT_ROOT/backend/.env.$env" "$PROJECT_ROOT/backend/.env"
    else
        echo "  ⚠️  Backend environment file not found: backend/.env.$env"
    fi

    # Frontend environment file
    if [ -f "$PROJECT_ROOT/frontend/.env.$env" ]; then
        echo "  Copying frontend/.env.$env to frontend/.env"
        cp "$PROJECT_ROOT/frontend/.env.$env" "$PROJECT_ROOT/frontend/.env"
    else
        echo "  ⚠️  Frontend environment file not found: frontend/.env.$env"
    fi
}

# Function to validate Stripe configuration
validate_stripe_config() {
    echo "🔍 Validating Stripe configuration..."

    # Check if validation script exists
    if [ -f "$SCRIPT_DIR/validate-environment.py" ]; then
        cd "$PROJECT_ROOT/backend"
        python3 "$SCRIPT_DIR/validate-environment.py" "$ENVIRONMENT"
    else
        echo "  ⚠️  Validation script not found, skipping validation"
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo "🎉 Environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update the environment files with your actual keys:"
    echo "   - backend/.env"
    echo "   - frontend/.env"
    echo ""
    echo "2. For Stripe configuration:"
    echo "   - Development: Use test keys (sk_test_*, pk_test_*)"
    echo "   - Staging: Use test keys with staging webhook endpoints"
    echo "   - Production: Use live keys (sk_live_*, pk_live_*)"
    echo ""
    echo "3. Set up Stripe webhooks:"
    case $ENVIRONMENT in
        development)
            echo "   - Use Stripe CLI: stripe listen --forward-to localhost:8000/api/stripe/webhook"
            ;;
        staging)
            echo "   - Configure webhook URL: https://api-staging.yourdomain.com/api/stripe/webhook"
            ;;
        production)
            echo "   - Configure webhook URL: https://api.yourdomain.com/api/stripe/webhook"
            echo "   - Enable webhook signature verification"
            ;;
    esac
    echo ""
    echo "4. Test the configuration:"
    echo "   - Run: docker compose up"
    echo "   - Verify Stripe integration works"
    echo "   - Test webhook delivery"
    echo ""
    echo "📚 For detailed configuration instructions, see:"
    echo "   docs/environment-configuration.md"
}

# Main execution
main() {
    copy_env_files "$ENVIRONMENT"

    echo ""
    echo "⚠️  IMPORTANT: Update the copied .env files with your actual API keys!"
    echo ""

    # Validate configuration (this will likely show errors until keys are updated)
    validate_stripe_config || true

    show_next_steps
}

# Run main function
main