"""
Configuration management for AI chat limits and plans.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AIChatPlanConfig:
    """AI chat plan configuration."""

    plan_name: str
    daily_limit: int
    description: str
    features: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "plan_name": self.plan_name,
            "daily_limit": self.daily_limit,
            "description": self.description,
            "features": self.features,
        }


class ConfigManager:
    """Configuration manager for AI chat plans."""

    def __init__(self):
        self.config_file = self._get_config_file_path()
        self._config_data = None
        self._ai_chat_plans = None
        self._last_modified = None

    def _get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return Path(__file__).parent / "ai_chat_limits.json"

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        if self._config_data is None:
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    self._config_data = json.load(f)
                # Update last modified time
                self._last_modified = os.path.getmtime(self.config_file)
            except (FileNotFoundError, json.JSONDecodeError):
                # Return default configuration if file doesn't exist or is invalid
                self._config_data = self._get_default_config()
                self._last_modified = None
        return self._config_data

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration when file is missing or invalid."""
        return {
            "ai_chat_plans": {
                "free": {
                    "daily_limit": 0,
                    "description": "Free plan - No AI chat access",
                    "features": ["Basic task management", "Manual task creation", "Google Calendar integration"],
                },
                "basic": {
                    "daily_limit": 10,
                    "description": "Basic plan - 10 AI chats per day",
                    "features": [
                        "Basic task management",
                        "AI chat assistance",
                        "Google integrations",
                        "Email task generation",
                        "Calendar task sync",
                    ],
                },
                "premium": {
                    "daily_limit": 50,
                    "description": "Premium plan - 50 AI chats per day",
                    "features": [
                        "All basic features",
                        "Priority support",
                        "Advanced AI features",
                        "Bulk task operations",
                        "Custom integrations",
                    ],
                },
                "enterprise": {
                    "daily_limit": -1,
                    "description": "Enterprise plan - Unlimited AI chats",
                    "features": [
                        "All premium features",
                        "Custom integrations",
                        "Dedicated support",
                        "Advanced analytics",
                        "Team collaboration",
                        "Custom workflows",
                    ],
                },
            },
            "settings": {
                "enable_dynamic_limits": True,
                "cache_duration_minutes": 5,
                "reset_timezone": "UTC",
                "enable_usage_analytics": True,
            },
            "last_updated": "2025-01-03T00:00:00Z",
        }

    def _load_plans(self) -> dict[str, AIChatPlanConfig]:
        """Load and cache AI chat plans."""
        if self._ai_chat_plans is None:
            config = self._load_config()
            plans = {}

            for plan_name, plan_data in config.get("ai_chat_plans", {}).items():
                # Check for environment variable override
                env_var_name = f"AI_CHAT_LIMIT_{plan_name.upper()}"
                daily_limit = plan_data.get("daily_limit", 0)

                # Override with environment variable if present and valid
                if env_var_name in os.environ:
                    try:
                        daily_limit = int(os.environ[env_var_name])
                    except ValueError:
                        # Keep original value if env var is invalid
                        daily_limit = plan_data.get("daily_limit", 0)

                plans[plan_name] = AIChatPlanConfig(
                    plan_name=plan_name,
                    daily_limit=daily_limit,
                    description=plan_data.get("description", ""),
                    features=plan_data.get("features", []),
                )

            self._ai_chat_plans = plans
        return self._ai_chat_plans

    def _save_config(self) -> None:
        """Save configuration to JSON file."""
        if self._config_data is not None:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            # Update last modified time
            self._last_modified = os.path.getmtime(self.config_file)

    def _save_to_file(self) -> None:
        """Alias for _save_config for backward compatibility."""
        self._save_config()

    def _check_file_updates(self) -> None:
        """Check if config file has been updated and reload if necessary."""
        try:
            if self.config_file.exists():
                current_modified = os.path.getmtime(self.config_file)
                if self._last_modified is None or current_modified > self._last_modified:
                    # File has been updated, clear cache to force reload
                    self._config_data = None
                    self._ai_chat_plans = None
                    self._last_modified = current_modified
        except OSError:
            # File access error, ignore
            pass

    def reload_config(self) -> None:
        """Force reload configuration from file."""
        self._config_data = None
        self._ai_chat_plans = None
        self._last_modified = None

    def reset_for_testing(self) -> None:
        """Reset config manager state for testing purposes."""
        self._config_data = None
        self._ai_chat_plans = None
        self._last_modified = None

    def get_all_plans(self) -> dict[str, AIChatPlanConfig]:
        """Get all AI chat plans."""
        return self._load_plans()

    def _ensure_plans_loaded(self) -> None:
        """Ensure plans are loaded into _ai_chat_plans attribute."""
        if self._ai_chat_plans is None:
            self._ai_chat_plans = self._load_plans()

    def get_plan_config(self, plan_name: str) -> AIChatPlanConfig | None:
        """Get configuration for a specific plan."""
        plans = self.get_all_plans()
        return plans.get(plan_name)

    def get_plan_limit(self, plan_name: str) -> int:
        """Get daily limit for a specific plan."""
        plan = self.get_plan_config(plan_name)
        return plan.daily_limit if plan else 0

    # Backward compatibility aliases
    def get_ai_chat_plan_limit(self, plan_name: str) -> int:
        """Get daily limit for a specific plan (alias)."""
        return self.get_plan_limit(plan_name)

    def get_ai_chat_plan_config(self, plan_name: str) -> AIChatPlanConfig | None:
        """Get configuration for a specific plan (alias)."""
        return self.get_plan_config(plan_name)

    def get_all_ai_chat_plans(self) -> dict[str, AIChatPlanConfig]:
        """Get all AI chat plans (alias)."""
        return self.get_all_plans()

    def update_ai_chat_plan_limit(
        self,
        plan_name: str,
        limit_or_daily_limit=None,
        description: str = None,
        features: list[str] = None,
        *,
        daily_limit: int = None,
        new_limit: int = None,
    ) -> bool:
        """Update daily limit for a specific plan (alias)."""
        # Support multiple calling patterns for backward compatibility
        if limit_or_daily_limit is not None:
            # Called with positional argument (old style)
            limit = limit_or_daily_limit
        elif daily_limit is not None:
            # Called with daily_limit keyword argument (new style)
            limit = daily_limit
        elif new_limit is not None:
            # Called with new_limit keyword argument (legacy)
            limit = new_limit
        else:
            raise ValueError("Either positional limit, daily_limit, or new_limit must be provided")
        return self.update_plan_limit(plan_name, limit, description, features)

    def update_plan_limit(
        self, plan_name: str, new_limit: int, description: str = None, features: list[str] = None
    ) -> bool:
        """Update daily limit for a specific plan."""
        # NOTE: Configuration file updates are disabled to prevent file pollution
        # Dynamic plan configuration should be handled through database or environment variables
        # This method is kept for backward compatibility but does not modify the config file
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Configuration file updates are disabled. Plan '{plan_name}' update ignored.")
        return False


# Global config manager instance
config_manager = ConfigManager()


# Convenience functions for backward compatibility
def get_all_ai_chat_plans() -> dict[str, AIChatPlanConfig]:
    """Get all AI chat plans."""
    return config_manager.get_all_plans()


def get_ai_chat_plan_config(plan_name: str) -> AIChatPlanConfig | None:
    """Get configuration for a specific AI chat plan."""
    return config_manager.get_plan_config(plan_name)


def get_ai_chat_plan_limit(plan_name: str) -> int:
    """Get daily limit for a specific AI chat plan."""
    return config_manager.get_plan_limit(plan_name)


def update_ai_chat_plan_limit(
    plan_name: str,
    limit_or_daily_limit=None,
    description: str = None,
    features: list[str] = None,
    *,
    daily_limit: int = None,
    new_limit: int = None,
) -> bool:
    """Update daily limit for a specific AI chat plan."""
    # Support multiple calling patterns for backward compatibility
    if limit_or_daily_limit is not None:
        # Called with positional argument (old style)
        limit = limit_or_daily_limit
    elif daily_limit is not None:
        # Called with daily_limit keyword argument (new style)
        limit = daily_limit
    elif new_limit is not None:
        # Called with new_limit keyword argument (legacy)
        limit = new_limit
    else:
        raise ValueError("Either positional limit, daily_limit, or new_limit must be provided")
    return config_manager.update_plan_limit(plan_name, limit, description, features)


def reset_config_for_testing() -> None:
    """Reset global config manager for testing purposes."""
    global config_manager
    config_manager.reset_for_testing()
