"""
Configuration management for AI chat limits and plans.
"""

import json
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


class ConfigManager:
    """Configuration manager for AI chat plans."""

    def __init__(self):
        self.config_file = Path(__file__).parent / "ai_chat_limits.json"
        self._config_data = None

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        if self._config_data is None:
            with open(self.config_file, encoding="utf-8") as f:
                self._config_data = json.load(f)
        return self._config_data

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
        config = self._load_config()
        plans = {}

        for plan_name, plan_data in config.get("ai_chat_plans", {}).items():
            plans[plan_name] = AIChatPlanConfig(
                plan_name=plan_name,
                daily_limit=plan_data.get("daily_limit", 0),
                description=plan_data.get("description", ""),
                features=plan_data.get("features", []),
            )

        return plans

    def get_plan_config(self, plan_name: str) -> AIChatPlanConfig | None:
        """Get configuration for a specific plan."""
        plans = self.get_all_plans()
        return plans.get(plan_name)

    def get_plan_limit(self, plan_name: str) -> int:
        """Get daily limit for a specific plan."""
        plan = self.get_plan_config(plan_name)
        return plan.daily_limit if plan else 0

    def update_plan_limit(self, plan_name: str, new_limit: int) -> bool:
        """Update daily limit for a specific plan."""
        config = self._load_config()

        if plan_name in config.get("ai_chat_plans", {}):
            config["ai_chat_plans"][plan_name]["daily_limit"] = new_limit
            self._save_config()
            # Clear cached data to force reload
            self._config_data = None
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
