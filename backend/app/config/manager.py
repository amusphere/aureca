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

    def _get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return Path(__file__).parent / "ai_chat_limits.json"

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        if self._config_data is None:
            with open(self.config_file, encoding="utf-8") as f:
                self._config_data = json.load(f)
        return self._config_data

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
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)

    def _save_to_file(self) -> None:
        """Alias for _save_config for backward compatibility."""
        self._save_config()

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
        self, plan_name: str, new_limit: int, description: str = None, features: list[str] = None
    ) -> bool:
        """Update daily limit for a specific plan (alias)."""
        return self.update_plan_limit(plan_name, new_limit)

    def update_plan_limit(self, plan_name: str, new_limit: int) -> bool:
        """Update daily limit for a specific plan."""
        config = self._load_config()

        if plan_name in config.get("ai_chat_plans", {}):
            config["ai_chat_plans"][plan_name]["daily_limit"] = new_limit
            self._save_config()
            # Clear cached data to force reload
            self._config_data = None
            self._ai_chat_plans = None
            return True

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


def update_ai_chat_plan_limit(plan_name: str, new_limit: int) -> bool:
    """Update daily limit for a specific AI chat plan."""
    return config_manager.update_plan_limit(plan_name, new_limit)
