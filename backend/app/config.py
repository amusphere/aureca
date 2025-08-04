"""
Configuration management for the application.

This module provides centralized configuration management with support for:
- Environment variables
- Configuration files
- Dynamic configuration updates
- Plan-based AI chat usage limits
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIChatPlanConfig:
    """Configuration for AI chat plan limits"""

    daily_limit: int
    description: str
    features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"daily_limit": self.daily_limit, "description": self.description, "features": self.features}


class ConfigManager:
    """
    Centralized configuration manager with support for dynamic updates
    """

    def __init__(self):
        self._config_cache: dict[str, Any] = {}
        self._config_file_path: Path | None = None
        self._last_modified: float | None = None
        self._ai_chat_plans: dict[str, AIChatPlanConfig] = {}

        # Initialize configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from environment variables and config files"""
        # Load from config file first if it exists
        config_file = self._get_config_file_path()
        if config_file and config_file.exists():
            self._load_from_file(config_file)

        # Load AI chat plan limits from environment or defaults (this will override file values)
        self._load_ai_chat_plans()

    def _get_config_file_path(self) -> Path | None:
        """Get the configuration file path"""
        # Check environment variable first
        config_path = os.getenv("AI_CHAT_CONFIG_FILE")
        if config_path:
            return Path(config_path)

        # Default to config file in app directory
        app_dir = Path(__file__).parent
        default_config = app_dir / "config" / "ai_chat_limits.json"

        return default_config if default_config.exists() else None

    def _load_ai_chat_plans(self) -> None:
        """Load AI chat plan configurations from environment variables or defaults"""
        # Default plan configurations
        default_plans = {
            "free": AIChatPlanConfig(
                daily_limit=0, description="Free plan - No AI chat access", features=["Basic task management"]
            ),
            "basic": AIChatPlanConfig(
                daily_limit=10,
                description="Basic plan - 10 AI chats per day",
                features=["Basic task management", "AI chat assistance", "Google integrations"],
            ),
            "premium": AIChatPlanConfig(
                daily_limit=50,
                description="Premium plan - 50 AI chats per day",
                features=["All basic features", "Priority support", "Advanced AI features"],
            ),
            "enterprise": AIChatPlanConfig(
                daily_limit=-1,  # Unlimited
                description="Enterprise plan - Unlimited AI chats",
                features=["All premium features", "Custom integrations", "Dedicated support"],
            ),
        }

        # Load from environment variables if available, preserving existing configurations
        for plan_name, default_config in default_plans.items():
            env_key = f"AI_CHAT_LIMIT_{plan_name.upper()}"
            env_limit = os.getenv(env_key)

            if env_limit is not None:
                try:
                    daily_limit = int(env_limit)
                    # Preserve existing configuration if available, otherwise use default
                    existing_config = self._ai_chat_plans.get(plan_name, default_config)
                    self._ai_chat_plans[plan_name] = AIChatPlanConfig(
                        daily_limit=daily_limit,
                        description=existing_config.description,
                        features=existing_config.features,
                    )
                    logger.info(f"Loaded {plan_name} plan limit from environment: {daily_limit}")
                except ValueError:
                    logger.warning(f"Invalid AI chat limit for {plan_name}: {env_limit}, using existing or default")
                    if plan_name not in self._ai_chat_plans:
                        self._ai_chat_plans[plan_name] = default_config
            else:
                # Only set default if no existing configuration
                if plan_name not in self._ai_chat_plans:
                    self._ai_chat_plans[plan_name] = default_config

    def _load_from_file(self, config_file: Path) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, encoding="utf-8") as f:
                file_config = json.load(f)

            # Update AI chat plans from file (will be overridden by environment variables later)
            if "ai_chat_plans" in file_config:
                for plan_name, plan_data in file_config["ai_chat_plans"].items():
                    self._ai_chat_plans[plan_name] = AIChatPlanConfig(
                        daily_limit=plan_data.get("daily_limit", 0),
                        description=plan_data.get("description", f"{plan_name} plan"),
                        features=plan_data.get("features", []),
                    )

            # Cache other configuration
            self._config_cache.update(file_config)
            self._config_file_path = config_file
            self._last_modified = config_file.stat().st_mtime

            logger.info(f"Loaded configuration from file: {config_file}")

        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")

    def _check_file_updates(self) -> None:
        """Check if configuration file has been updated and reload if necessary"""
        if not self._config_file_path or not self._config_file_path.exists():
            return

        try:
            current_mtime = self._config_file_path.stat().st_mtime
            if self._last_modified is None or current_mtime > self._last_modified:
                logger.info("Configuration file updated, reloading...")
                self._load_from_file(self._config_file_path)
        except Exception as e:
            logger.error(f"Failed to check configuration file updates: {e}")

    def get_ai_chat_plan_limit(self, plan_name: str) -> int:
        """
        Get daily AI chat limit for a specific plan

        Args:
            plan_name: Name of the subscription plan

        Returns:
            int: Daily limit (-1 for unlimited, 0 for no access)
        """
        self._check_file_updates()

        plan_config = self._ai_chat_plans.get(plan_name)
        if plan_config:
            return plan_config.daily_limit

        # Default to free plan if unknown plan
        logger.warning(f"Unknown plan '{plan_name}', defaulting to free plan")
        return self._ai_chat_plans.get("free", AIChatPlanConfig(0, "Unknown plan")).daily_limit

    def get_ai_chat_plan_config(self, plan_name: str) -> AIChatPlanConfig | None:
        """
        Get full configuration for a specific plan

        Args:
            plan_name: Name of the subscription plan

        Returns:
            AIChatPlanConfig or None if plan not found
        """
        self._check_file_updates()
        return self._ai_chat_plans.get(plan_name)

    def get_all_ai_chat_plans(self) -> dict[str, AIChatPlanConfig]:
        """
        Get all AI chat plan configurations

        Returns:
            Dict mapping plan names to their configurations
        """
        self._check_file_updates()
        return self._ai_chat_plans.copy()

    def update_ai_chat_plan_limit(
        self, plan_name: str, daily_limit: int, description: str = None, features: list[str] = None
    ) -> bool:
        """
        Update AI chat plan limit dynamically

        Args:
            plan_name: Name of the plan to update
            daily_limit: New daily limit
            description: Optional description update
            features: Optional features list update

        Returns:
            bool: True if update was successful
        """
        try:
            existing_config = self._ai_chat_plans.get(plan_name)

            if existing_config:
                # Update existing plan
                self._ai_chat_plans[plan_name] = AIChatPlanConfig(
                    daily_limit=daily_limit,
                    description=description or existing_config.description,
                    features=features or existing_config.features,
                )
            else:
                # Create new plan
                self._ai_chat_plans[plan_name] = AIChatPlanConfig(
                    daily_limit=daily_limit, description=description or f"{plan_name} plan", features=features or []
                )

            # Save to file if configured
            if self._config_file_path:
                self._save_to_file()

            logger.info(f"Updated AI chat plan '{plan_name}' with limit: {daily_limit}")
            return True

        except Exception as e:
            logger.error(f"Failed to update AI chat plan '{plan_name}': {e}")
            return False

    def _save_to_file(self) -> None:
        """Save current configuration to file"""
        if not self._config_file_path:
            return

        try:
            # Ensure directory exists
            self._config_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare configuration data
            config_data = {
                **self._config_cache,  # Start with cached config
                "ai_chat_plans": {
                    plan_name: plan_config.to_dict() for plan_name, plan_config in self._ai_chat_plans.items()
                },
                "last_updated": datetime.now().isoformat(),
            }

            # Write to file
            with open(self._config_file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self._last_modified = self._config_file_path.stat().st_mtime
            logger.info(f"Saved configuration to file: {self._config_file_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to file: {e}")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        self._check_file_updates()
        return self._config_cache.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config_cache[key] = value

        # Save to file if configured
        if self._config_file_path:
            self._save_to_file()


# Global configuration manager instance
config_manager = ConfigManager()


def get_ai_chat_plan_limit(plan_name: str) -> int:
    """
    Convenience function to get AI chat plan limit

    Args:
        plan_name: Name of the subscription plan

    Returns:
        int: Daily limit (-1 for unlimited, 0 for no access)
    """
    return config_manager.get_ai_chat_plan_limit(plan_name)


def get_ai_chat_plan_config(plan_name: str) -> AIChatPlanConfig | None:
    """
    Convenience function to get AI chat plan configuration

    Args:
        plan_name: Name of the subscription plan

    Returns:
        AIChatPlanConfig or None if plan not found
    """
    return config_manager.get_ai_chat_plan_config(plan_name)


def get_all_ai_chat_plans() -> dict[str, AIChatPlanConfig]:
    """
    Convenience function to get all AI chat plan configurations

    Returns:
        Dict mapping plan names to their configurations
    """
    return config_manager.get_all_ai_chat_plans()


def update_ai_chat_plan_limit(
    plan_name: str, daily_limit: int, description: str = None, features: list[str] = None
) -> bool:
    """
    Convenience function to update AI chat plan limit

    Args:
        plan_name: Name of the plan to update
        daily_limit: New daily limit
        description: Optional description update
        features: Optional features list update

    Returns:
        bool: True if update was successful
    """
    return config_manager.update_ai_chat_plan_limit(plan_name, daily_limit, description, features)
