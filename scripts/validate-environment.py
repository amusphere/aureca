#!/usr/bin/env python3
"""
Environment validation script for Stripe billing migration.

This script validates that all required environment variables are properly
configured for the specified environment (development, staging, production).
"""

import os
import sys
from typing import List, Tuple


def validate_stripe_keys(secret_key: str, publishable_key: str) -> List[str]:
    """Validate that Stripe keys are from the same environment."""
    errors = []

    if not secret_key or not publishable_key:
        errors.append("Both STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY are required")
        return errors

    # Check if keys are from the same environment
    secret_is_test = secret_key.startswith("sk_test_")
    publishable_is_test = publishable_key.startswith("pk_test_")

    if secret_is_test != publishable_is_test:
        errors.append(
            "Stripe secret key and publishable key are from different environments"
        )

    # Validate key formats
    if not (secret_key.startswith("sk_test_") or secret_key.startswith("sk_live_")):
        errors.append("Invalid STRIPE_SECRET_KEY format")

    if not (
        publishable_key.startswith("pk_test_") or publishable_key.startswith("pk_live_")
    ):
        errors.append("Invalid STRIPE_PUBLISHABLE_KEY format")

    return errors


def validate_environment_variables(environment: str) -> Tuple[List[str], List[str]]:
    """Validate environment variables for the specified environment."""
    errors = []
    warnings = []

    # Required backend variables
    backend_required = [
        "APP_NAME",
        "DATABASE_URL",
        "FRONTEND_URL",
        "CLERK_SECRET_KEY",
        "OPENAI_API_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ]

    # Check backend variables
    for var in backend_required:
        if not os.getenv(var):
            errors.append(f"Missing required backend environment variable: {var}")

    # Validate Stripe configuration
    stripe_secret = os.getenv("STRIPE_SECRET_KEY")
    stripe_publishable = os.getenv("STRIPE_PUBLISHABLE_KEY")

    if stripe_secret and stripe_publishable:
        stripe_errors = validate_stripe_keys(stripe_secret, stripe_publishable)
        errors.extend(stripe_errors)

        # Environment-specific validation
        is_test_mode = stripe_secret.startswith("sk_test_")

        if environment == "production" and is_test_mode:
            errors.append("Production environment should use live Stripe keys")
        elif environment in ["development", "staging"] and not is_test_mode:
            warnings.append(
                f"{environment.title()} environment should typically use test Stripe keys"
            )

    # Check webhook secret
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if webhook_secret and not webhook_secret.startswith("whsec_"):
        errors.append("Invalid STRIPE_WEBHOOK_SECRET format")

    # Check optional Stripe variables
    api_version = os.getenv("STRIPE_API_VERSION", "2023-10-16")
    if api_version != "2023-10-16":
        warnings.append(f"Using non-default Stripe API version: {api_version}")

    # Check Google OAuth configuration
    google_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
    missing_google = [var for var in google_vars if not os.getenv(var)]
    if missing_google:
        warnings.append(
            f"Google OAuth not fully configured. Missing: {', '.join(missing_google)}"
        )

    return errors, warnings


def print_validation_results(environment: str, errors: List[str], warnings: List[str]):
    """Print validation results in a formatted way."""
    print(f"\n🔍 Environment Validation Results for: {environment.upper()}")
    print("=" * 60)

    if not errors and not warnings:
        print("✅ All environment variables are properly configured!")
        return

    if errors:
        print("\n❌ ERRORS (must be fixed):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")

    if warnings:
        print("\n⚠️  WARNINGS (should be reviewed):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    if errors:
        print(f"\n❌ Validation failed with {len(errors)} error(s)")
        sys.exit(1)
    else:
        print(f"\n✅ Validation passed with {len(warnings)} warning(s)")


def main():
    """Main validation function."""
    if len(sys.argv) != 2:
        print("Usage: python validate-environment.py <environment>")
        print("Environment options: development, staging, production")
        sys.exit(1)

    environment = sys.argv[1].lower()

    if environment not in ["development", "staging", "production"]:
        print("Invalid environment. Use: development, staging, or production")
        sys.exit(1)

    print(f"🚀 Validating environment configuration for: {environment}")

    # Load environment file if it exists
    env_file = f".env.{environment}"
    if os.path.exists(env_file):
        print(f"📁 Found environment file: {env_file}")
        # Note: In a real deployment, you might want to load this file
        # For now, we'll just validate what's currently in the environment

    errors, warnings = validate_environment_variables(environment)
    print_validation_results(environment, errors, warnings)


if __name__ == "__main__":
    main()
