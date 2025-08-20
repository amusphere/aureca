"""
Database configuration settings.

This module contains all database-related configuration including
connection URLs and database-specific settings.
"""

import os


class DatabaseConfig:
    """Database configuration settings."""

    URL: str = os.getenv("DATABASE_URL", "sqlite:///./test_database.db")

    @classmethod
    def get_connection_args(cls) -> dict:
        """Get database connection arguments."""
        args = {"future": True}

        # Add PostgreSQL specific settings if using PostgreSQL
        if cls.URL.startswith("postgresql"):
            args.update(
                {
                    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
                    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
                }
            )

        return args

    @classmethod
    def is_sqlite(cls) -> bool:
        """Check if using SQLite database."""
        return cls.URL.startswith("sqlite")

    @classmethod
    def is_postgresql(cls) -> bool:
        """Check if using PostgreSQL database."""
        return cls.URL.startswith("postgresql")
