"""
Stripe service for handling subscription and payment operations.

This service provides a centralized interface for all Stripe operations
including customer management, subscription handling, and webhook processing.
"""

import logging

import stripe

from app.config.stripe import StripeConfig

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe operations."""

    def __init__(self, raise_on_missing_config: bool = True):
        """
        Initialize Stripe service with API configuration.

        Args:
            raise_on_missing_config: If True, raises an error when Stripe is not configured.
                                   If False, allows initialization but operations will fail.
        """
        self._configured = StripeConfig.is_configured()

        if not self._configured:
            if raise_on_missing_config:
                raise ValueError(
                    "Stripe is not properly configured. Please set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY environment variables."
                )
            else:
                logger.warning("Stripe service initialized without proper configuration")
                return

        # Set the Stripe API key
        stripe.api_key = StripeConfig.SECRET_KEY

        # Log configuration status
        if StripeConfig.is_test_mode():
            logger.info("Stripe service initialized in TEST mode")
        else:
            logger.info("Stripe service initialized in LIVE mode")

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return self._configured

    async def verify_api_connection(self) -> bool:
        """
        Verify that the Stripe API connection is working.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        if not self._configured:
            logger.error("Cannot verify API connection: Stripe is not configured")
            return False

        try:
            # Make a simple API call to verify connection
            account = stripe.Account.retrieve()
            logger.info(f"Stripe API connection verified. Account ID: {account.id}")
            return True
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication failed: {e}")
            return False
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error verifying Stripe connection: {e}")
            return False

    def get_publishable_key(self) -> str | None:
        """
        Get the Stripe publishable key for frontend use.

        Returns:
            Optional[str]: The publishable key if configured, None otherwise
        """
        return StripeConfig.PUBLISHABLE_KEY

    def is_test_mode(self) -> bool:
        """
        Check if Stripe is running in test mode.

        Returns:
            bool: True if in test mode, False if in live mode
        """
        return StripeConfig.is_test_mode()


# Global instance for dependency injection
stripe_service = StripeService(raise_on_missing_config=False)
