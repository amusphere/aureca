"""
Authentication configuration settings.

This module contains all authentication-related configuration including
Clerk, OAuth, and other auth provider settings.
"""

import os


class ClerkConfig:
    """Clerk authentication configuration."""

    SECRET_KEY: str | None = os.getenv("CLERK_SECRET_KEY")
    WEBHOOK_SECRET: str | None = os.getenv("CLERK_WEBHOOK_SECRET")

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Clerk is properly configured."""
        return bool(cls.SECRET_KEY)


class GoogleOAuthConfig:
    """Google OAuth configuration."""

    CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/api/auth/google/callback")
    ENCRYPTION_KEY: str | None = os.getenv("GOOGLE_OAUTH_ENCRYPTION_KEY")

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(cls.CLIENT_ID and cls.CLIENT_SECRET and cls.ENCRYPTION_KEY)


class AuthConfig:
    """General authentication configuration."""

    SYSTEM: str = os.getenv("AUTH_SYSTEM", "clerk")
    SECRET_KEY: str | None = os.getenv("SECRET_KEY")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    @classmethod
    def get_authorized_parties(cls) -> list[str]:
        """Get list of authorized parties for JWT validation."""
        return [cls.FRONTEND_URL]

    @classmethod
    def is_clerk_enabled(cls) -> bool:
        """Check if Clerk authentication is enabled."""
        return cls.SYSTEM == "clerk"

    @classmethod
    def is_email_password_enabled(cls) -> bool:
        """Check if email/password authentication is enabled."""
        return cls.SYSTEM == "email_password"
