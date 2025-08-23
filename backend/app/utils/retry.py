"""
Retry utilities for handling transient failures.

This module provides retry mechanisms with exponential backoff
for handling temporary failures in external service calls.
"""

import asyncio
import logging
import random
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: list[type[Exception]] | None = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            retryable_exceptions: List of exceptions that should trigger retries
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            float: Delay in seconds
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter to avoid thundering herd
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-based)

        Returns:
            bool: True if should retry, False otherwise
        """
        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False

        # Check if exception is retryable
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)


def retry_async(config: RetryConfig) -> Callable:
    """
    Decorator for async functions with retry logic.

    Args:
        config: Retry configuration

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not config.should_retry(e, attempt):
                        logger.error(
                            f"Function {func.__name__} failed after {attempt + 1} attempts: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                        )
                        raise

                    # Calculate delay for next attempt
                    if attempt < config.max_attempts - 1:  # Don't delay after last attempt
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt + 1}, retrying in {delay:.2f}s: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "delay": delay,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                        )
                        await asyncio.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def retry_sync(config: RetryConfig) -> Callable:
    """
    Decorator for sync functions with retry logic.

    Args:
        config: Retry configuration

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time

            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not config.should_retry(e, attempt):
                        logger.error(
                            f"Function {func.__name__} failed after {attempt + 1} attempts: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                        )
                        raise

                    # Calculate delay for next attempt
                    if attempt < config.max_attempts - 1:  # Don't delay after last attempt
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Function {func.__name__} failed on attempt {attempt + 1}, retrying in {delay:.2f}s: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "delay": delay,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                        )
                        time.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# Predefined retry configurations
WEBHOOK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        # Add specific exceptions that should trigger retries
    ],
)

STRIPE_API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        # Stripe-specific retryable exceptions will be added when we import stripe
    ],
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    max_delay=5.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        # Database-specific exceptions will be added
    ],
)
