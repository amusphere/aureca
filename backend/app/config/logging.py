"""
Logging configuration for the application.

This module provides structured logging configuration with different
levels and formatters for development and production environments.
"""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Any


class SecurityEventFilter(logging.Filter):
    """Filter for security-related log events."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter security events for special handling.

        Args:
            record: The log record to filter

        Returns:
            bool: True to include the record, False to exclude
        """
        # Mark security events for special handling
        security_keywords = [
            "signature verification failed",
            "invalid signature",
            "authentication failed",
            "unauthorized access",
            "security",
            "webhook signature",
        ]

        message = record.getMessage().lower()
        for keyword in security_keywords:
            if keyword in message:
                record.security_event = True
                return True

        return True


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: The log record to format

        Returns:
            str: JSON-formatted log message
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        # Mark security events
        if hasattr(record, "security_event"):
            log_data["security_event"] = True

        return json.dumps(log_data, default=str, ensure_ascii=False)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def __init__(self):
        """Initialize development formatter with colors."""
        super().__init__()
        self.colors = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
            "RESET": "\033[0m",  # Reset
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record for development.

        Args:
            record: The log record to format

        Returns:
            str: Formatted log message
        """
        # Color the level name
        level_color = self.colors.get(record.levelname, "")
        reset_color = self.colors["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Base format
        formatted = f"{timestamp} {level_color}{record.levelname:8}{reset_color} {record.name:20} {record.getMessage()}"

        # Add exception information if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                extra_fields[key] = value

        if extra_fields:
            formatted += f" | {extra_fields}"

        # Mark security events
        if hasattr(record, "security_event"):
            formatted += f" {self.colors['ERROR']}[SECURITY]{reset_color}"

        return formatted


def get_logging_config() -> dict[str, Any]:
    """
    Get logging configuration based on environment.

    Returns:
        Dict: Logging configuration dictionary
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "security_filter": {
                "()": SecurityEventFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "filters": ["security_filter"],
            },
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # Stripe-specific logger
            "app.services.stripe_service": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app.services.stripe_webhook_handler": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app.routers.api.stripe": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # Third-party loggers
            "stripe": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    # Environment-specific configuration
    if environment == "production":
        # Production: JSON structured logging
        config["formatters"] = {
            "structured": {
                "()": StructuredFormatter,
            },
        }
        config["handlers"]["console"]["formatter"] = "structured"

        # Add file handler for production
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/app/application.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "structured",
            "filters": ["security_filter"],
        }

        # Add security event handler
        config["handlers"]["security"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/app/security.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "structured",
            "level": "WARNING",
        }

        # Update loggers to use file handlers
        for logger_name in config["loggers"]:
            if logger_name.startswith("app"):
                config["loggers"][logger_name]["handlers"] = ["console", "file"]

    else:
        # Development: Human-readable logging
        config["formatters"] = {
            "development": {
                "()": DevelopmentFormatter,
            },
        }
        config["handlers"]["console"]["formatter"] = "development"

    return config


def setup_logging() -> None:
    """Set up logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Log startup information
    logger = logging.getLogger("app.config.logging")
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logger.info(f"Logging configured for {environment} environment with level {log_level}")


def get_security_logger() -> logging.Logger:
    """
    Get a logger specifically for security events.

    Returns:
        logging.Logger: Security event logger
    """
    logger = logging.getLogger("app.security")
    logger.addFilter(SecurityEventFilter())
    return logger


def log_security_event(
    event_type: str,
    message: str,
    details: dict[str, Any] = None,
    user_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
) -> None:
    """
    Log a security event with structured data.

    Args:
        event_type: Type of security event
        message: Security event message
        details: Additional event details
        user_id: User ID if applicable
        ip_address: Client IP address if applicable
        user_agent: Client user agent if applicable
    """
    logger = get_security_logger()

    extra_data = {
        "security_event": True,
        "event_type": event_type,
        "details": details or {},
    }

    if user_id:
        extra_data["user_id"] = user_id
    if ip_address:
        extra_data["ip_address"] = ip_address
    if user_agent:
        extra_data["user_agent"] = user_agent

    logger.warning(message, extra=extra_data)


# Initialize logging when module is imported
setup_logging()
