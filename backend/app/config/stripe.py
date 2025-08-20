"""
Stripe configuration settings.

This module contains all Stripe-related configuration including
API keys, webhook secrets, and utility methods for Stripe setup.
"""

import os


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
    def get_api_version(cls) -> str:
        """Get the Stripe API version to use."""
        return os.getenv("STRIPE_API_VERSION", "2023-10-16")

    @classmethod
    def get_webhook_tolerance(cls) -> int:
        """Get webhook timestamp tolerance in seconds."""
        return int(os.getenv("STRIPE_WEBHOOK_TOLERANCE", "300"))
