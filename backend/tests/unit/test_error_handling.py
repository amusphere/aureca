"""
Tests for error handling and logging functionality.

This module tests the custom exception classes, retry mechanisms,
and logging configuration to ensure proper error handling.
"""

from unittest.mock import Mock, patch

import pytest
from stripe import error as stripe_error

from app.config.logging import get_security_logger, log_security_event
from app.utils.exceptions import (
    BaseAppException,
    DatabaseException,
    RateLimitException,
    StripeConfigurationException,
    StripeServiceException,
    StripeSignatureException,
    StripeWebhookException,
    SubscriptionNotFoundException,
    UserNotFoundException,
    ValidationException,
)
from app.utils.retry import RetryConfig, retry_async, retry_sync


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_base_app_exception(self):
        """Test BaseAppException initialization and properties."""
        exc = BaseAppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            user_message="User friendly message",
        )

        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.user_message == "User friendly message"
        assert str(exc) == "Test error"

    def test_base_app_exception_defaults(self):
        """Test BaseAppException with default values."""
        exc = BaseAppException("Test error")

        assert exc.message == "Test error"
        assert exc.error_code == "BaseAppException"
        assert exc.details == {}
        assert exc.user_message == "An unexpected error occurred. Please try again."

    def test_stripe_service_exception(self):
        """Test StripeServiceException with Stripe error."""
        stripe_error_mock = stripe_error.InvalidRequestError("Invalid request", "param")

        exc = StripeServiceException(
            message="Stripe service failed",
            stripe_error=stripe_error_mock,
            error_code="STRIPE_TEST_ERROR",
            user_message="Payment failed",
        )

        assert exc.message == "Stripe service failed"
        assert exc.error_code == "STRIPE_TEST_ERROR"
        assert exc.user_message == "Payment failed"
        assert exc.stripe_error == stripe_error_mock
        assert exc.details["stripe_error_type"] == "InvalidRequestError"
        assert exc.details["stripe_error_message"] == "Invalid request"

    def test_stripe_configuration_exception(self):
        """Test StripeConfigurationException."""
        exc = StripeConfigurationException(
            message="Missing config",
            missing_config="STRIPE_SECRET_KEY",
        )

        assert exc.message == "Missing config"
        assert exc.error_code == "STRIPE_CONFIG_ERROR"
        assert exc.details["missing_config"] == "STRIPE_SECRET_KEY"
        assert "not properly configured" in exc.user_message

    def test_stripe_webhook_exception(self):
        """Test StripeWebhookException."""
        exc = StripeWebhookException(
            message="Webhook failed",
            event_id="evt_123",
            event_type="customer.subscription.created",
            retry_count=2,
        )

        assert exc.message == "Webhook failed"
        assert exc.error_code == "STRIPE_WEBHOOK_ERROR"
        assert exc.event_id == "evt_123"
        assert exc.event_type == "customer.subscription.created"
        assert exc.retry_count == 2
        assert exc.details["event_id"] == "evt_123"
        assert exc.details["retry_count"] == 2

    def test_stripe_signature_exception(self):
        """Test StripeSignatureException."""
        signature = "t=1234567890,v1=abcdefghijklmnopqrstuvwxyz"

        exc = StripeSignatureException(
            message="Invalid signature",
            signature=signature,
        )

        assert exc.message == "Invalid signature"
        assert exc.error_code == "STRIPE_SIGNATURE_ERROR"
        assert exc.details["signature_prefix"] == "t=12345678..."

    def test_subscription_not_found_exception(self):
        """Test SubscriptionNotFoundException."""
        exc = SubscriptionNotFoundException("sub_123", "stripe_id")

        assert exc.message == "Subscription not found with stripe_id: sub_123"
        assert exc.error_code == "SUBSCRIPTION_NOT_FOUND"
        assert exc.details["identifier"] == "sub_123"
        assert exc.details["identifier_type"] == "stripe_id"

    def test_user_not_found_exception(self):
        """Test UserNotFoundException."""
        exc = UserNotFoundException("user@example.com", "email")

        assert exc.message == "User not found with email: user@example.com"
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.details["identifier"] == "user@example.com"
        assert exc.details["identifier_type"] == "email"

    def test_database_exception(self):
        """Test DatabaseException."""
        exc = DatabaseException(
            message="Database error",
            operation="create",
            table="subscriptions",
        )

        assert exc.message == "Database error"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details["operation"] == "create"
        assert exc.details["table"] == "subscriptions"

    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException(
            message="Invalid email format",
            field="email",
            value="invalid-email",
        )

        assert exc.message == "Invalid email format"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"
        assert exc.user_message == "Invalid email: Invalid email format"

    def test_validation_exception_long_value(self):
        """Test ValidationException with long value truncation."""
        long_value = "a" * 100

        exc = ValidationException(
            message="Value too long",
            field="description",
            value=long_value,
        )

        assert exc.details["value"] == "a" * 50 + "..."

    def test_rate_limit_exception(self):
        """Test RateLimitException."""
        exc = RateLimitException(
            message="Rate limit exceeded",
            retry_after=60,
        )

        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.details["retry_after"] == 60
        assert "60 seconds" in exc.user_message


class TestRetryMechanism:
    """Test retry mechanism functionality."""

    def test_retry_config_defaults(self):
        """Test RetryConfig default values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == [Exception]

    def test_retry_config_calculate_delay(self):
        """Test delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)

        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0

    def test_retry_config_calculate_delay_with_max(self):
        """Test delay calculation with max delay."""
        config = RetryConfig(base_delay=10.0, max_delay=15.0, exponential_base=2.0, jitter=False)

        assert config.calculate_delay(0) == 10.0
        assert config.calculate_delay(1) == 15.0  # Capped at max_delay
        assert config.calculate_delay(2) == 15.0  # Capped at max_delay

    def test_retry_config_should_retry(self):
        """Test retry decision logic."""
        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError])

        # Should retry for retryable exception within max attempts
        assert config.should_retry(ValueError("test"), 0) is True
        assert config.should_retry(ValueError("test"), 2) is True

        # Should not retry after max attempts
        assert config.should_retry(ValueError("test"), 3) is False

        # Should not retry for non-retryable exception
        assert config.should_retry(TypeError("test"), 0) is False

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test async retry decorator with successful function."""
        config = RetryConfig(max_attempts=3)
        call_count = 0

        @retry_async(config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_with_retries(self):
        """Test async retry decorator with retries."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError])
        call_count = 0

        @retry_async(config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_max_attempts_exceeded(self):
        """Test async retry decorator when max attempts exceeded."""
        config = RetryConfig(max_attempts=2, base_delay=0.01, retryable_exceptions=[ValueError])
        call_count = 0

        @retry_async(config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            await test_func()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_non_retryable_exception(self):
        """Test async retry decorator with non-retryable exception."""
        config = RetryConfig(max_attempts=3, retryable_exceptions=[ValueError])
        call_count = 0

        @retry_async(config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable error")

        with pytest.raises(TypeError, match="Non-retryable error"):
            await test_func()

        assert call_count == 1

    def test_retry_sync_success(self):
        """Test sync retry decorator with successful function."""
        config = RetryConfig(max_attempts=3)
        call_count = 0

        @retry_sync(config)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_sync_with_retries(self):
        """Test sync retry decorator with retries."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError])
        call_count = 0

        @retry_sync(config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3


class TestLogging:
    """Test logging functionality."""

    @patch("app.config.logging.get_security_logger")
    def test_log_security_event(self, mock_get_logger):
        """Test security event logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_security_event(
            event_type="test_event",
            message="Test security event",
            details={"key": "value"},
            user_id="user123",
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args

        assert call_args[0][0] == "Test security event"
        extra_data = call_args[1]["extra"]
        assert extra_data["security_event"] is True
        assert extra_data["event_type"] == "test_event"
        assert extra_data["details"] == {"key": "value"}
        assert extra_data["user_id"] == "user123"
        assert extra_data["ip_address"] == "192.168.1.1"
        assert extra_data["user_agent"] == "test-agent"

    @patch("app.config.logging.get_security_logger")
    def test_log_security_event_minimal(self, mock_get_logger):
        """Test security event logging with minimal parameters."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_security_event(
            event_type="test_event",
            message="Test security event",
        )

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args

        assert call_args[0][0] == "Test security event"
        extra_data = call_args[1]["extra"]
        assert extra_data["security_event"] is True
        assert extra_data["event_type"] == "test_event"
        assert extra_data["details"] == {}
        assert "user_id" not in extra_data
        assert "ip_address" not in extra_data
        assert "user_agent" not in extra_data

    def test_get_security_logger(self):
        """Test security logger creation."""
        logger = get_security_logger()

        assert logger.name == "app.security"
        # Check that security filter is added
        assert len(logger.filters) > 0
