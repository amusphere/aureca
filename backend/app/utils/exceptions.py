"""
Custom exception classes for the application.

This module defines custom exceptions for better error handling
and user experience across the application.
"""

from typing import Any


class BaseAppException(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ):
        """
        Initialize base application exception.

        Args:
            message: Technical error message for logging
            error_code: Unique error code for identification
            details: Additional error details
            user_message: User-friendly error message
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.user_message = user_message or "An unexpected error occurred. Please try again."


class StripeServiceException(BaseAppException):
    """Exception raised for Stripe service errors."""

    def __init__(
        self,
        message: str,
        stripe_error: Exception | None = None,
        error_code: str | None = None,
        user_message: str | None = None,
    ):
        """
        Initialize Stripe service exception.

        Args:
            message: Technical error message
            stripe_error: Original Stripe error
            error_code: Unique error code
            user_message: User-friendly message
        """
        details = {}
        if stripe_error:
            details["stripe_error_type"] = type(stripe_error).__name__
            details["stripe_error_message"] = str(stripe_error)

        super().__init__(
            message=message,
            error_code=error_code or "STRIPE_SERVICE_ERROR",
            details=details,
            user_message=user_message or "Payment service is temporarily unavailable. Please try again later.",
        )
        self.stripe_error = stripe_error


class StripeConfigurationException(StripeServiceException):
    """Exception raised for Stripe configuration errors."""

    def __init__(self, message: str, missing_config: str | None = None):
        """
        Initialize Stripe configuration exception.

        Args:
            message: Technical error message
            missing_config: Name of missing configuration
        """
        details = {}
        if missing_config:
            details["missing_config"] = missing_config

        super().__init__(
            message=message,
            error_code="STRIPE_CONFIG_ERROR",
            user_message="Payment service is not properly configured. Please contact support.",
        )
        self.details.update(details)


class StripeWebhookException(StripeServiceException):
    """Exception raised for Stripe webhook processing errors."""

    def __init__(
        self,
        message: str,
        event_id: str | None = None,
        event_type: str | None = None,
        retry_count: int = 0,
    ):
        """
        Initialize Stripe webhook exception.

        Args:
            message: Technical error message
            event_id: Stripe event ID
            event_type: Stripe event type
            retry_count: Number of retry attempts
        """
        details = {
            "retry_count": retry_count,
        }
        if event_id:
            details["event_id"] = event_id
        if event_type:
            details["event_type"] = event_type

        super().__init__(
            message=message,
            error_code="STRIPE_WEBHOOK_ERROR",
            user_message="Payment status update failed. Your subscription status will be updated shortly.",
        )
        self.details.update(details)
        self.event_id = event_id
        self.event_type = event_type
        self.retry_count = retry_count


class StripeSignatureException(StripeServiceException):
    """Exception raised for Stripe webhook signature verification errors."""

    def __init__(self, message: str, signature: str | None = None):
        """
        Initialize Stripe signature exception.

        Args:
            message: Technical error message
            signature: The invalid signature (truncated for security)
        """
        details = {}
        if signature:
            # Only log first 10 characters for security
            details["signature_prefix"] = signature[:10] + "..." if len(signature) > 10 else signature

        super().__init__(
            message=message,
            error_code="STRIPE_SIGNATURE_ERROR",
            user_message="Invalid webhook signature. This request has been rejected for security reasons.",
        )
        self.details.update(details)


class SubscriptionNotFoundException(BaseAppException):
    """Exception raised when a subscription is not found."""

    def __init__(self, identifier: str, identifier_type: str = "id"):
        """
        Initialize subscription not found exception.

        Args:
            identifier: The identifier that was not found
            identifier_type: Type of identifier (id, stripe_id, user_id)
        """
        message = f"Subscription not found with {identifier_type}: {identifier}"
        details = {
            "identifier": identifier,
            "identifier_type": identifier_type,
        }

        super().__init__(
            message=message,
            error_code="SUBSCRIPTION_NOT_FOUND",
            details=details,
            user_message="Subscription not found. Please check your subscription status.",
        )


class UserNotFoundException(BaseAppException):
    """Exception raised when a user is not found."""

    def __init__(self, identifier: str, identifier_type: str = "id"):
        """
        Initialize user not found exception.

        Args:
            identifier: The identifier that was not found
            identifier_type: Type of identifier (id, email, stripe_customer_id)
        """
        message = f"User not found with {identifier_type}: {identifier}"
        details = {
            "identifier": identifier,
            "identifier_type": identifier_type,
        }

        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details=details,
            user_message="User account not found. Please check your account status.",
        )


class DatabaseException(BaseAppException):
    """Exception raised for database operation errors."""

    def __init__(self, message: str, operation: str | None = None, table: str | None = None):
        """
        Initialize database exception.

        Args:
            message: Technical error message
            operation: Database operation (create, update, delete, select)
            table: Database table name
        """
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            user_message="A database error occurred. Please try again later.",
        )


class ValidationException(BaseAppException):
    """Exception raised for data validation errors."""

    def __init__(self, message: str, field: str | None = None, value: Any | None = None):
        """
        Initialize validation exception.

        Args:
            message: Technical error message
            field: Field name that failed validation
            value: Invalid value (will be sanitized)
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            # Sanitize sensitive values
            if isinstance(value, str) and len(value) > 50:
                details["value"] = value[:50] + "..."
            else:
                details["value"] = str(value)

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            user_message=f"Invalid {field}: {message}" if field else message,
        )


class RateLimitException(BaseAppException):
    """Exception raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        """
        Initialize rate limit exception.

        Args:
            message: Technical error message
            retry_after: Seconds to wait before retrying
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            user_message=f"Too many requests. Please try again in {retry_after} seconds."
            if retry_after
            else "Too many requests. Please try again later.",
        )
