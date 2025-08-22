"""
Stripe configuration settings.

This module contains all Stripe-related configuration including
API keys, webhook secrets, and utility methods for Stripe setup.
"""

import os
from typing import Literal


class StripeConfig:
    """Stripe configuration settings."""

    SECRET_KEY: str | None = os.getenv("STRIPE_SECRET_KEY")
    PUBLISHABLE_KEY: str | None = os.getenv("STRIPE_PUBLISHABLE_KEY")
    WEBHOOK_SECRET: str | None = os.getenv("STRIPE_WEBHOOK_SECRET")

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Stripe is properly configured."""
        return bool(cls.SECRET_KEY and cls.PUBLISHABLE_KEY)

    @classmethod
    def is_test_mode(cls) -> bool:
        """Check if Stripe is in test mode."""
        return bool(cls.SECRET_KEY and cls.SECRET_KEY.startswith("sk_test_"))

    @classmethod
    def is_live_mode(cls) -> bool:
        """Check if Stripe is in live mode."""
        return bool(cls.SECRET_KEY and cls.SECRET_KEY.startswith("sk_live_"))

    @classmethod
    def get_environment(cls) -> Literal["test", "live", "unknown"]:
        """Get the current Stripe environment."""
        if cls.is_test_mode():
            return "test"
        elif cls.is_live_mode():
            return "live"
        return "unknown"

    @classmethod
    def get_api_version(cls) -> str:
        """Get the Stripe API version to use."""
        return os.getenv("STRIPE_API_VERSION", "2023-10-16")

    @classmethod
    def get_webhook_tolerance(cls) -> int:
        """Get webhook timestamp tolerance in seconds."""
        return int(os.getenv("STRIPE_WEBHOOK_TOLERANCE", "300"))

    @classmethod
    def validate_configuration(cls) -> dict[str, str | bool]:
        """Validate the current Stripe configuration."""
        validation_result = {
            "is_configured": cls.is_configured(),
            "environment": cls.get_environment(),
            "has_webhook_secret": bool(cls.WEBHOOK_SECRET),
            "api_version": cls.get_api_version(),
            "webhook_tolerance": cls.get_webhook_tolerance(),
        }

        # Add warnings for common misconfigurations
        warnings = []
        if cls.SECRET_KEY and cls.PUBLISHABLE_KEY:
            secret_env = "test" if cls.SECRET_KEY.startswith("sk_test_") else "live"
            publishable_env = "test" if cls.PUBLISHABLE_KEY.startswith("pk_test_") else "live"

            if secret_env != publishable_env:
                warnings.append("Secret key and publishable key are from different environments")

        if not cls.WEBHOOK_SECRET:
            warnings.append("Webhook secret is not configured")

        validation_result["warnings"] = warnings
        return validation_result
