"""
Application configuration settings.

This module contains general application configuration including
app name, URLs, and other application-wide settings.
"""

import os


class AppConfig:
    """Application configuration settings."""

    NAME: str = os.getenv("APP_NAME", "Nadeshiko.AI")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment."""
        return cls.ENVIRONMENT == "development"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.ENVIRONMENT == "production"

    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment."""
        return cls.ENVIRONMENT == "testing"


class OpenAIConfig:
    """OpenAI API configuration."""

    API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    @classmethod
    def is_configured(cls) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(cls.API_KEY)
