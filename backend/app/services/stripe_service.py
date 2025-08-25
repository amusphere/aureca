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

from app.config.logging import log_security_event
from app.config.stripe import StripeConfig
from app.schema import User
from app.utils.exceptions import (
    StripeConfigurationException,
    StripeServiceException,
    StripeSignatureException,
)
from app.utils.retry import RetryConfig, retry_async

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
                raise StripeConfigurationException(
                    "Stripe is not properly configured. Please set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY environment variables.",
                    missing_config="STRIPE_SECRET_KEY or STRIPE_PUBLISHABLE_KEY",
                )
            else:
                logger.warning("Stripe service initialized without proper configuration")
                return

        # Set the Stripe API key
        stripe.api_key = StripeConfig.SECRET_KEY

        # Note: Retry configuration with Stripe-specific exceptions is handled
        # within individual method decorators to avoid import issues

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

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If API connection fails
        """
        if not self._configured:
            raise StripeConfigurationException("Cannot verify API connection: Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _verify_connection():
            try:
                # Make a simple API call to verify connection
                account = stripe.Account.retrieve()
                logger.info(f"Stripe API connection verified. Account ID: {account.id}")
                return True
            except stripe_error.AuthenticationError as e:
                log_security_event(
                    event_type="stripe_authentication_failed",
                    message=f"Stripe authentication failed: {e}",
                    details={"error_type": type(e).__name__, "error_message": str(e)},
                )
                raise StripeServiceException(
                    f"Stripe authentication failed: {e}",
                    stripe_error=e,
                    error_code="STRIPE_AUTH_ERROR",
                    user_message="Payment service authentication failed. Please contact support.",
                ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Stripe API error during connection verification: {e}")
                raise StripeServiceException(
                    f"Stripe API error: {e}",
                    stripe_error=e,
                    error_code="STRIPE_API_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error verifying Stripe connection: {e}")
                raise StripeServiceException(
                    f"Unexpected error verifying Stripe connection: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CONNECTION_ERROR",
                ) from e

        return await _verify_connection()

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
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If customer creation fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _create_customer():
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

                logger.info(
                    f"Created Stripe customer {customer.id} for user {user.id}",
                    extra={
                        "user_id": user.id,
                        "stripe_customer_id": customer.id,
                        "operation": "create_customer",
                    },
                )
                return customer.id

            except stripe_error.InvalidRequestError as e:
                logger.error(f"Invalid request creating Stripe customer for user {user.id}: {e}")
                raise StripeServiceException(
                    f"Invalid request creating Stripe customer: {e}",
                    stripe_error=e,
                    error_code="STRIPE_INVALID_REQUEST",
                    user_message="Invalid customer information. Please check your account details.",
                ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
                raise StripeServiceException(
                    f"Failed to create Stripe customer: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CUSTOMER_CREATE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error creating Stripe customer for user {user.id}: {e}")
                raise StripeServiceException(
                    f"Unexpected error creating Stripe customer: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CUSTOMER_CREATE_UNEXPECTED",
                ) from e

        return await _create_customer()

    async def get_customer(self, stripe_customer_id: str) -> stripe.Customer:
        """
        Retrieve a Stripe customer by ID.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            stripe.Customer: The customer object

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If customer retrieval fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _get_customer():
            try:
                customer = stripe.Customer.retrieve(stripe_customer_id)
                logger.debug(
                    f"Retrieved Stripe customer {stripe_customer_id}",
                    extra={
                        "stripe_customer_id": stripe_customer_id,
                        "operation": "get_customer",
                    },
                )
                return customer

            except stripe_error.InvalidRequestError as e:
                if "No such customer" in str(e):
                    logger.warning(f"Stripe customer not found: {stripe_customer_id}")
                    raise StripeServiceException(
                        f"Stripe customer not found: {stripe_customer_id}",
                        stripe_error=e,
                        error_code="STRIPE_CUSTOMER_NOT_FOUND",
                        user_message="Customer account not found. Please contact support.",
                    ) from e
                else:
                    logger.error(f"Invalid request retrieving Stripe customer {stripe_customer_id}: {e}")
                    raise StripeServiceException(
                        f"Invalid request retrieving Stripe customer: {e}",
                        stripe_error=e,
                        error_code="STRIPE_INVALID_REQUEST",
                    ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Failed to retrieve Stripe customer {stripe_customer_id}: {e}")
                raise StripeServiceException(
                    f"Failed to retrieve Stripe customer: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CUSTOMER_RETRIEVE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error retrieving Stripe customer {stripe_customer_id}: {e}")
                raise StripeServiceException(
                    f"Unexpected error retrieving Stripe customer: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CUSTOMER_RETRIEVE_UNEXPECTED",
                ) from e

        return await _get_customer()

    # Subscription Management Methods

    async def get_customer_subscriptions(self, stripe_customer_id: str) -> list[stripe.Subscription]:
        """
        Retrieve all subscriptions for a Stripe customer.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            list[stripe.Subscription]: List of customer subscriptions

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If subscription retrieval fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _get_subscriptions():
            try:
                subscriptions = stripe.Subscription.list(
                    customer=stripe_customer_id,
                    limit=100,  # Get all subscriptions for the customer
                    expand=["data.default_payment_method"],
                )

                logger.debug(
                    f"Retrieved {len(subscriptions.data)} subscriptions for customer {stripe_customer_id}",
                    extra={
                        "stripe_customer_id": stripe_customer_id,
                        "subscription_count": len(subscriptions.data),
                        "operation": "get_customer_subscriptions",
                    },
                )
                return subscriptions.data

            except stripe_error.InvalidRequestError as e:
                logger.error(f"Invalid request retrieving subscriptions for customer {stripe_customer_id}: {e}")
                raise StripeServiceException(
                    f"Invalid request retrieving subscriptions: {e}",
                    stripe_error=e,
                    error_code="STRIPE_INVALID_REQUEST",
                ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Failed to retrieve subscriptions for customer {stripe_customer_id}: {e}")
                raise StripeServiceException(
                    f"Failed to retrieve subscriptions: {e}",
                    stripe_error=e,
                    error_code="STRIPE_SUBSCRIPTION_RETRIEVE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error retrieving subscriptions for customer {stripe_customer_id}: {e}")
                raise StripeServiceException(
                    f"Unexpected error retrieving subscriptions: {e}",
                    stripe_error=e,
                    error_code="STRIPE_SUBSCRIPTION_RETRIEVE_UNEXPECTED",
                ) from e

        return await _get_subscriptions()

    async def get_active_subscription(self, stripe_customer_id: str) -> stripe.Subscription | None:
        """
        Get the active subscription for a customer (if any).

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            stripe.Subscription | None: The active subscription or None if no active subscription

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If subscription retrieval fails
        """
        subscriptions = await self.get_customer_subscriptions(stripe_customer_id)

        # Find the first active subscription
        for subscription in subscriptions:
            if subscription.status in ["active", "trialing"]:
                logger.debug(
                    f"Found active subscription {subscription.id} for customer {stripe_customer_id}",
                    extra={
                        "stripe_customer_id": stripe_customer_id,
                        "subscription_id": subscription.id,
                        "subscription_status": subscription.status,
                        "operation": "get_active_subscription",
                    },
                )
                return subscription

        logger.debug(
            f"No active subscription found for customer {stripe_customer_id}",
            extra={
                "stripe_customer_id": stripe_customer_id,
                "operation": "get_active_subscription",
            },
        )
        return None

    # Checkout and Portal Session Methods

    async def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str, mode: str = "subscription"
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for subscription purchase.

        Args:
            customer_id: The Stripe customer ID
            price_id: The Stripe price ID for the subscription
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled
            mode: Checkout mode (default: "subscription")

        Returns:
            stripe.checkout.Session: The created checkout session

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If checkout session creation fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _create_checkout_session():
            try:
                session_data = {
                    "customer": customer_id,
                    "line_items": [
                        {
                            "price": price_id,
                            "quantity": 1,
                        }
                    ],
                    "mode": mode,
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "allow_promotion_codes": True,
                    "billing_address_collection": "auto",
                }

                # Add subscription-specific settings
                if mode == "subscription":
                    session_data.update(
                        {
                            "subscription_data": {
                                "metadata": {
                                    "customer_id": customer_id,
                                }
                            }
                        }
                    )

                session = stripe.checkout.Session.create(**session_data)

                logger.info(
                    f"Created checkout session {session.id} for customer {customer_id}",
                    extra={
                        "stripe_customer_id": customer_id,
                        "checkout_session_id": session.id,
                        "price_id": price_id,
                        "mode": mode,
                        "operation": "create_checkout_session",
                    },
                )
                return session

            except stripe_error.InvalidRequestError as e:
                logger.error(f"Invalid request creating checkout session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Invalid request creating checkout session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_INVALID_REQUEST",
                    user_message="Invalid checkout configuration. Please try again or contact support.",
                ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Failed to create checkout session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Failed to create checkout session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CHECKOUT_CREATE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error creating checkout session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Unexpected error creating checkout session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_CHECKOUT_CREATE_UNEXPECTED",
                ) from e

        return await _create_checkout_session()

    async def create_customer_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """
        Create a Stripe Customer Portal session for subscription management.

        Args:
            customer_id: The Stripe customer ID
            return_url: URL to redirect to when the customer leaves the portal

        Returns:
            stripe.billing_portal.Session: The created portal session

        Raises:
            StripeConfigurationException: If Stripe is not configured
            StripeServiceException: If portal session creation fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        # Create local retry config with Stripe-specific exceptions
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=[
                stripe_error.RateLimitError,
                stripe_error.APIConnectionError,
                stripe_error.APIError,
                ConnectionError,
                TimeoutError,
            ],
        )

        @retry_async(retry_config)
        async def _create_portal_session():
            try:
                session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url=return_url,
                )

                logger.info(
                    f"Created customer portal session {session.id} for customer {customer_id}",
                    extra={
                        "stripe_customer_id": customer_id,
                        "portal_session_id": session.id,
                        "operation": "create_customer_portal_session",
                    },
                )
                return session

            except stripe_error.InvalidRequestError as e:
                logger.error(f"Invalid request creating portal session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Invalid request creating portal session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_INVALID_REQUEST",
                    user_message="Unable to access customer portal. Please contact support.",
                ) from e
            except stripe_error.StripeError as e:
                logger.error(f"Failed to create portal session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Failed to create portal session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_PORTAL_CREATE_ERROR",
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error creating portal session for customer {customer_id}: {e}")
                raise StripeServiceException(
                    f"Unexpected error creating portal session: {e}",
                    stripe_error=e,
                    error_code="STRIPE_PORTAL_CREATE_UNEXPECTED",
                ) from e

        return await _create_portal_session()

    # Utility Methods

    def is_subscription_active(self, subscription: stripe.Subscription) -> bool:
        """
        Check if a subscription is considered active.

        Args:
            subscription: The Stripe subscription object

        Returns:
            bool: True if subscription is active, False otherwise
        """
        return subscription.status in ["active", "trialing"]

    def is_subscription_premium(self, subscription: stripe.Subscription | None) -> bool:
        """
        Check if a subscription provides premium access.

        Args:
            subscription: The Stripe subscription object or None

        Returns:
            bool: True if subscription provides premium access, False otherwise
        """
        if not subscription:
            return False

        return self.is_subscription_active(subscription)

    def get_subscription_plan_name(self, subscription: stripe.Subscription | None) -> str | None:
        """
        Get the plan name from a subscription.

        Args:
            subscription: The Stripe subscription object or None

        Returns:
            str | None: The plan name or None if no subscription
        """
        if not subscription or not subscription.items.data:
            return None

        # Get the first item's price nickname or product name
        item = subscription.items.data[0]
        if item.price.nickname:
            return item.price.nickname

        # Fallback to product name if available
        if hasattr(item.price, "product") and hasattr(item.price.product, "name"):
            return item.price.product.name

        return f"Plan {item.price.id}"

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
            StripeConfigurationException: If webhook secret is not configured
            StripeSignatureException: If signature verification fails
            StripeServiceException: If event construction fails
        """
        if not self._configured:
            raise StripeConfigurationException("Stripe is not configured")

        if not StripeConfig.WEBHOOK_SECRET:
            raise StripeConfigurationException(
                "Stripe webhook secret is not configured", missing_config="STRIPE_WEBHOOK_SECRET"
            )

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, StripeConfig.WEBHOOK_SECRET, tolerance=StripeConfig.get_webhook_tolerance()
            )

            logger.debug(
                f"Verified webhook event {event['id']} of type {event['type']}",
                extra={
                    "event_id": event["id"],
                    "event_type": event["type"],
                    "operation": "verify_webhook_signature",
                },
            )
            return event

        except stripe_error.SignatureVerificationError as e:
            # Log security event for signature verification failure
            log_security_event(
                event_type="webhook_signature_verification_failed",
                message=f"Webhook signature verification failed: {e}",
                details={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "signature_prefix": signature[:10] + "..." if len(signature) > 10 else signature,
                },
            )
            raise StripeSignatureException(f"Webhook signature verification failed: {e}", signature=signature) from e
        except Exception as e:
            logger.error(f"Unexpected error verifying webhook signature: {e}")
            raise StripeServiceException(
                f"Unexpected error verifying webhook signature: {e}",
                stripe_error=e,
                error_code="STRIPE_WEBHOOK_VERIFY_ERROR",
            ) from e

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
