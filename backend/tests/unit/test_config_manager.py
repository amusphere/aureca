"""
Unit tests for configuration management system
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import AIChatPlanConfig, ConfigManager


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    config_data = {
        "ai_chat_plans": {
            "free": {
                "daily_limit": 0,
                "description": "Free plan - No AI chat access",
                "features": ["Basic task management"],
            },
            "basic": {
                "daily_limit": 10,
                "description": "Basic plan - 10 AI chats per day",
                "features": [
                    "Basic task management",
                    "AI chat assistance",
                    "Google integrations",
                ],
            },
            "premium": {
                "daily_limit": 50,
                "description": "Premium plan - 50 AI chats per day",
                "features": [
                    "All basic features",
                    "Priority support",
                    "Advanced AI features",
                ],
            },
            "enterprise": {
                "daily_limit": -1,
                "description": "Enterprise plan - Unlimited AI chats",
                "features": [
                    "All premium features",
                    "Custom integrations",
                    "Dedicated support",
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

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name

    yield Path(temp_file)

    # Cleanup
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass


@pytest.fixture
def isolated_config_manager(temp_config_file):
    """Create an isolated config manager for testing"""
    with patch.object(
        ConfigManager, "_get_config_file_path", return_value=temp_config_file
    ):
        return ConfigManager()


class TestAIChatPlanConfig:
    """Test AIChatPlanConfig dataclass"""

    def test_plan_config_creation(self):
        """Test creating a plan configuration"""
        config = AIChatPlanConfig(
            daily_limit=10, description="Test plan", features=["feature1", "feature2"]
        )

        assert config.daily_limit == 10
        assert config.description == "Test plan"
        assert config.features == ["feature1", "feature2"]

    def test_plan_config_to_dict(self):
        """Test converting plan configuration to dictionary"""
        config = AIChatPlanConfig(
            daily_limit=50,
            description="Premium plan",
            features=["ai_chat", "integrations"],
        )

        result = config.to_dict()
        expected = {
            "daily_limit": 50,
            "description": "Premium plan",
            "features": ["ai_chat", "integrations"],
        }

        assert result == expected


class TestConfigManager:
    """Test ConfigManager class"""

    def test_default_plan_loading(self, isolated_config_manager):
        """Test that default plans are loaded correctly"""
        config_manager = isolated_config_manager

        # Check that default plans exist
        assert "free" in config_manager._ai_chat_plans
        assert "basic" in config_manager._ai_chat_plans
        assert "premium" in config_manager._ai_chat_plans
        assert "enterprise" in config_manager._ai_chat_plans

        # Check default limits
        assert config_manager._ai_chat_plans["free"].daily_limit == 0
        assert config_manager._ai_chat_plans["basic"].daily_limit == 10
        assert config_manager._ai_chat_plans["premium"].daily_limit == 50
        assert config_manager._ai_chat_plans["enterprise"].daily_limit == -1

    @patch.dict(os.environ, {"AI_CHAT_LIMIT_BASIC": "20"})
    def test_environment_variable_override(self, temp_config_file):
        """Test that environment variables override default limits"""
        with patch.object(
            ConfigManager, "_get_config_file_path", return_value=temp_config_file
        ):
            config_manager = ConfigManager()

        # Basic plan should be overridden by environment variable
        assert config_manager._ai_chat_plans["basic"].daily_limit == 20

    @patch.dict(os.environ, {"AI_CHAT_LIMIT_BASIC": "invalid"})
    def test_invalid_environment_variable(self, temp_config_file):
        """Test handling of invalid environment variable values"""
        with patch.object(
            ConfigManager, "_get_config_file_path", return_value=temp_config_file
        ):
            config_manager = ConfigManager()

        # Should fall back to default value when environment variable is invalid
        assert config_manager._ai_chat_plans["basic"].daily_limit == 10

    def test_get_ai_chat_plan_limit(self, isolated_config_manager):
        """Test getting plan limits"""
        config_manager = isolated_config_manager

        assert config_manager.get_ai_chat_plan_limit("free") == 0
        assert config_manager.get_ai_chat_plan_limit("basic") == 10
        assert config_manager.get_ai_chat_plan_limit("premium") == 50
        assert config_manager.get_ai_chat_plan_limit("enterprise") == -1

        # Unknown plan should default to free
        assert config_manager.get_ai_chat_plan_limit("unknown") == 0

    def test_get_ai_chat_plan_config(self, isolated_config_manager):
        """Test getting full plan configuration"""
        config_manager = isolated_config_manager

        basic_config = config_manager.get_ai_chat_plan_config("basic")
        assert basic_config is not None
        assert basic_config.daily_limit == 10
        assert "Basic plan" in basic_config.description
        assert len(basic_config.features) > 0

        # Unknown plan should return None
        unknown_config = config_manager.get_ai_chat_plan_config("unknown")
        assert unknown_config is None

    def test_update_ai_chat_plan_limit(self, isolated_config_manager):
        """Test updating plan limits"""
        config_manager = isolated_config_manager

        # Update existing plan
        success = config_manager.update_ai_chat_plan_limit(
            "basic", 15, "Updated basic plan", ["new_feature"]
        )
        assert success is True

        updated_config = config_manager.get_ai_chat_plan_config("basic")
        assert updated_config.daily_limit == 15
        assert updated_config.description == "Updated basic plan"
        assert updated_config.features == ["new_feature"]

        # Create new plan
        success = config_manager.update_ai_chat_plan_limit(
            "custom", 25, "Custom plan", ["custom_feature"]
        )
        assert success is True

        custom_config = config_manager.get_ai_chat_plan_config("custom")
        assert custom_config is not None
        assert custom_config.daily_limit == 25

    def test_get_all_ai_chat_plans(self, isolated_config_manager):
        """Test getting all plan configurations"""
        config_manager = isolated_config_manager

        all_plans = config_manager.get_all_ai_chat_plans()

        assert isinstance(all_plans, dict)
        assert len(all_plans) >= 4  # At least the default plans
        assert "free" in all_plans
        assert "basic" in all_plans
        assert "premium" in all_plans
        assert "enterprise" in all_plans

    def test_config_file_loading(self):
        """Test loading configuration from file"""
        # Create temporary config file
        config_data = {
            "ai_chat_plans": {
                "test_plan": {
                    "daily_limit": 100,
                    "description": "Test plan from file",
                    "features": ["test_feature"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            # Mock the config file path
            with patch.object(
                ConfigManager, "_get_config_file_path", return_value=Path(temp_file)
            ):
                config_manager = ConfigManager()

                # Check that the test plan was loaded
                test_config = config_manager.get_ai_chat_plan_config("test_plan")
                assert test_config is not None
                assert test_config.daily_limit == 100
                assert test_config.description == "Test plan from file"
                assert test_config.features == ["test_feature"]

        finally:
            # Clean up temporary file
            os.unlink(temp_file)

    def test_config_file_updates(self):
        """Test dynamic configuration file updates"""
        # Create temporary config file
        config_data = {
            "ai_chat_plans": {
                "dynamic_plan": {
                    "daily_limit": 30,
                    "description": "Original plan",
                    "features": ["original_feature"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            # Mock the config file path
            with patch.object(
                ConfigManager, "_get_config_file_path", return_value=Path(temp_file)
            ):
                config_manager = ConfigManager()

                # Check initial configuration
                initial_config = config_manager.get_ai_chat_plan_config("dynamic_plan")
                assert initial_config.daily_limit == 30

                # Update the file
                updated_config_data = {
                    "ai_chat_plans": {
                        "dynamic_plan": {
                            "daily_limit": 40,
                            "description": "Updated plan",
                            "features": ["updated_feature"],
                        }
                    }
                }

                with open(temp_file, "w") as f:
                    json.dump(updated_config_data, f)

                # Force check for updates
                config_manager._check_file_updates()

                # Check updated configuration
                updated_config = config_manager.get_ai_chat_plan_config("dynamic_plan")
                assert updated_config.daily_limit == 40
                assert updated_config.description == "Updated plan"
                assert updated_config.features == ["updated_feature"]

        finally:
            # Clean up temporary file
            os.unlink(temp_file)


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_ai_chat_plan_limit_function(self, isolated_config_manager):
        """Test the convenience function for getting plan limits"""
        # Use isolated config manager to avoid global state issues
        limit = isolated_config_manager.get_ai_chat_plan_limit("basic")
        assert limit == 10

        limit = isolated_config_manager.get_ai_chat_plan_limit("unknown")
        assert limit == 0  # Should default to free plan


class TestConfigManagerIntegration:
    """Integration tests for configuration manager"""

    def test_environment_and_file_precedence(self):
        """Test that environment variables take precedence over file configuration"""
        # Create config file with one value
        config_data = {
            "ai_chat_plans": {
                "basic": {
                    "daily_limit": 5,
                    "description": "File basic plan",
                    "features": ["file_feature"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            # Set environment variable with different value
            with patch.dict(os.environ, {"AI_CHAT_LIMIT_BASIC": "15"}):
                with patch.object(
                    ConfigManager, "_get_config_file_path", return_value=Path(temp_file)
                ):
                    config_manager = ConfigManager()

                    # Environment variable should take precedence
                    basic_config = config_manager.get_ai_chat_plan_config("basic")
                    assert basic_config.daily_limit == 15  # From environment
                    # But other properties should come from file
                    assert basic_config.description == "File basic plan"
                    assert basic_config.features == ["file_feature"]

        finally:
            # Clean up temporary file
            os.unlink(temp_file)

    def test_error_handling(self):
        """Test error handling in configuration management"""
        # Test with invalid JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            with patch.object(
                ConfigManager, "_get_config_file_path", return_value=Path(temp_file)
            ):
                # Should not raise exception, should fall back to defaults
                config_manager = ConfigManager()

                # Should still have default plans
                assert config_manager.get_ai_chat_plan_limit("basic") == 10

        finally:
            # Clean up temporary file
            os.unlink(temp_file)
