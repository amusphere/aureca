"""
Stripe service for handling subscription and payment operations.

This service provides a centralized interface for all Stripe operations
including customer management, subscription handling, and webhook processing.
"""

import hashlib
import hmac
import logging

import stripe
from stripe import error as stripe_error

from app.config.stripe import StripeConfig
from app.schema import User

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
        except stripe_error.AuthenticationError as e:
            logger.error(f"Stripe authentication failed: {e}")
            return False
        except stripe_error.StripeError as e:
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

    # Customer Management Methods

    async def create_customer(self, user: User) -> str:
        """
        Create a new Stripe customer for the given user.

        Args:
            user: The user to create a customer for

        Returns:
            str: The Stripe customer ID

        Raises:
            stripe.error.StripeError: If customer creation fails
        """
        if not self._configured:
            raise ValueError("Stripe is not configured")

        try:
            customer_data = {
                "email": user.email,
                "metadata": {
                    "user_id": str(user.id),
                    "user_uuid": str(user.uuid),
                },
            }

            # Add name if available
            if user.name:
                customer_data["name"] = user.name

            customer = stripe.Customer.create(**customer_data)

            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id

        except stripe_error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe customer for user {user.id}: {e}")
            raise

    async def get_customer(self, stripe_customer_id: str) -> stripe.Customer:
        """
        Retrieve a Stripe customer by ID.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            stripe.Customer: The customer object

        Raises:
            stripe.error.StripeError: If customer retrieval fails
        """
        if not self._configured:
            raise ValueError("Stripe is not configured")

        try:
            customer = stripe.Customer.retrieve(stripe_customer_id)
            logger.debug(f"Retrieved Stripe customer {stripe_customer_id}")
            return customer

        except stripe_error.StripeError as e:
            logger.error(f"Failed to retrieve Stripe customer {stripe_customer_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving Stripe customer {stripe_customer_id}: {e}")
            raise

    # Webhook Methods

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> stripe.Event:
        """
        Verify webhook signature and construct Stripe event.

        Args:
            payload: The raw request body from Stripe
            signature: The Stripe-Signature header value

        Returns:
            stripe.Event: The verified Stripe event

        Raises:
            stripe.error.SignatureVerificationError: If signature verification fails
            ValueError: If webhook secret is not configured
        """
        if not self._configured:
            raise ValueError("Stripe is not configured")

        if not StripeConfig.WEBHOOK_SECRET:
            raise ValueError("Stripe webhook secret is not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, StripeConfig.WEBHOOK_SECRET, tolerance=StripeConfig.get_webhook_tolerance()
            )

            logger.debug(f"Verified webhook event {event['id']} of type {event['type']}")
            return event

        except stripe_error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error verifying webhook signature: {e}")
            raise

    def _verify_webhook_signature_manual(self, payload: bytes, signature: str) -> bool:
        """
        Manual webhook signature verification (fallback method).

        Args:
            payload: The raw request body from Stripe
            signature: The Stripe-Signature header value

        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not StripeConfig.WEBHOOK_SECRET:
            logger.error("Cannot verify webhook signature: webhook secret not configured")
            return False

        try:
            # Parse the signature header
            elements = signature.split(",")
            signature_dict = {}

            for element in elements:
                key, value = element.split("=", 1)
                signature_dict[key] = value

            timestamp = signature_dict.get("t")
            v1_signature = signature_dict.get("v1")

            if not timestamp or not v1_signature:
                logger.error("Invalid signature format")
                return False

            # Create the signed payload
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"

            # Compute the expected signature
            expected_signature = hmac.new(
                StripeConfig.WEBHOOK_SECRET.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(expected_signature, v1_signature)

        except Exception as e:
            logger.error(f"Error in manual signature verification: {e}")
            return False


# Global instance for dependency injection
stripe_service = StripeService(raise_on_missing_config=False)
