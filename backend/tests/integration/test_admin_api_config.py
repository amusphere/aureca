"""
Integration tests for admin configuration API endpoints
"""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config.manager import AIChatPlanConfig, config_manager
from main import app

client = TestClient(app)


def generate_unique_plan_name(base_name="test_plan"):
    """Generate a unique plan name for testing"""
    return f"{base_name}_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def mock_config_manager():
    """Mock config manager to use in-memory data instead of files"""
    # Create test data
    test_plans = {
        "free": AIChatPlanConfig(
            plan_name="free",
            daily_limit=0,
            description="Free plan - No AI chat access",
            features=[
                "Basic task management",
                "Manual task creation",
                "Google Calendar integration",
            ],
        ),
        "basic": AIChatPlanConfig(
            plan_name="basic",
            daily_limit=10,
            description="Basic plan - 10 AI chats per day",
            features=[
                "Basic task management",
                "AI chat assistance",
                "Google integrations",
                "Email task generation",
                "Calendar task sync",
            ],
        ),
        "premium": AIChatPlanConfig(
            plan_name="premium",
            daily_limit=50,
            description="Premium plan - 50 AI chats per day",
            features=[
                "All basic features",
                "Priority support",
                "Advanced AI features",
                "Bulk task operations",
                "Custom integrations",
            ],
        ),
        "enterprise": AIChatPlanConfig(
            plan_name="enterprise",
            daily_limit=-1,
            description="Enterprise plan - Unlimited AI chats",
            features=[
                "All premium features",
                "Custom integrations",
                "Dedicated support",
                "Advanced analytics",
                "Team collaboration",
                "Custom workflows",
            ],
        ),
    }

    # Mock the config manager methods
    with (
        patch.object(config_manager, "_ai_chat_plans", test_plans),
        patch.object(config_manager, "_save_to_file", return_value=None),
    ):
        yield


class TestAdminAIChatPlansAPI:
    """Test admin API endpoints for AI chat plan management"""

    def test_get_all_ai_chat_plans(self):
        """Test getting all AI chat plans via API"""
        response = client.get("/api/admin/ai-chat/plans")

        assert response.status_code == 200
        data = response.json()

        assert "plans" in data
        assert "total_plans" in data
        assert isinstance(data["plans"], dict)
        assert data["total_plans"] >= 4  # At least default plans

        # Check that default plans are present
        assert "free" in data["plans"]
        assert "basic" in data["plans"]
        assert "premium" in data["plans"]
        assert "enterprise" in data["plans"]

        # Check plan structure
        basic_plan = data["plans"]["basic"]
        assert "plan_name" in basic_plan
        assert "daily_limit" in basic_plan
        assert "description" in basic_plan
        assert "features" in basic_plan
        assert basic_plan["daily_limit"] == 10

    def test_get_specific_ai_chat_plan(self):
        """Test getting a specific AI chat plan via API"""
        response = client.get("/api/admin/ai-chat/plans/basic")

        assert response.status_code == 200
        data = response.json()

        assert data["plan_name"] == "basic"
        assert data["daily_limit"] == 10
        assert "Basic plan" in data["description"]
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0

    def test_get_nonexistent_plan(self):
        """Test getting a non-existent plan returns appropriate response"""
        response = client.get("/api/admin/ai-chat/plans/nonexistent")

        # Should still return a response (defaults to free plan)
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "free"  # Should default to free

    def test_update_ai_chat_plan(self):
        """Test updating an AI chat plan via API"""
        update_data = {
            "plan_name": "basic",
            "daily_limit": 15,
            "description": "Updated basic plan",
            "features": ["updated_feature1", "updated_feature2"],
        }

        response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "update ignored" in data["message"]
        assert data["plan_name"] == "basic"
        assert "warning" in data
        assert "database-based configuration" in data["warning"]

    def test_update_plan_with_invalid_limit(self):
        """Test updating a plan with invalid daily limit"""
        update_data = {
            "plan_name": "basic",
            "daily_limit": -2,  # Invalid: must be -1 or non-negative
            "description": "Invalid plan",
        }

        response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)

        assert response.status_code == 400
        data = response.json()
        assert "Daily limit must be -1" in data["detail"]

    def test_create_new_ai_chat_plan(self):
        """Test creating a new AI chat plan via API"""
        unique_plan_name = generate_unique_plan_name("test_plan")
        new_plan_data = {
            "plan_name": unique_plan_name,
            "daily_limit": 25,
            "description": "Test plan created via API",
            "features": ["test_feature1", "test_feature2"],
        }

        response = client.post("/api/admin/ai-chat/plans", json=new_plan_data)

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "creation ignored" in data["message"]
        assert data["plan_name"] == unique_plan_name
        assert "warning" in data
        assert "database-based configuration" in data["warning"]

    def test_create_duplicate_plan(self):
        """Test creating a plan that already exists"""
        duplicate_plan_data = {
            "plan_name": "basic",  # Already exists
            "daily_limit": 20,
            "description": "Duplicate plan",
        }

        response = client.post("/api/admin/ai-chat/plans", json=duplicate_plan_data)

        # Now returns 200 with warning instead of 409
        assert response.status_code == 200
        data = response.json()
        assert "creation ignored" in data["message"]

    def test_create_plan_with_invalid_limit(self):
        """Test creating a plan with invalid daily limit"""
        invalid_plan_data = {
            "plan_name": "invalid_plan",
            "daily_limit": -5,  # Invalid
            "description": "Invalid plan",
        }

        response = client.post("/api/admin/ai-chat/plans", json=invalid_plan_data)

        assert response.status_code == 400
        data = response.json()
        assert "Daily limit must be -1" in data["detail"]

    def test_reload_config_endpoint(self):
        """Test the configuration reload endpoint"""
        response = client.get("/api/admin/ai-chat/config/reload")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Configuration" in data["message"] and "reloaded" in data["message"]
        assert "timestamp" in data


class TestAdminAPIIntegration:
    """Integration tests for admin API with configuration system"""

    def test_api_reflects_config_changes(self):
        """Test that API endpoints return warning for configuration changes"""
        # Update the plan via API
        update_data = {
            "plan_name": "basic",
            "daily_limit": 15,
            "description": "API integration test plan",
        }

        update_response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)
        assert update_response.status_code == 200

        # Verify warning message is returned
        update_data = update_response.json()
        assert "update ignored" in update_data["message"]
        assert "warning" in update_data

        # Verify the configuration remains unchanged
        assert config_manager.get_ai_chat_plan_limit("basic") == 10  # Original value

    def test_unlimited_plan_handling(self):
        """Test handling of unlimited plans (-1 limit)"""
        # Create an unlimited plan
        unique_plan_name = generate_unique_plan_name("unlimited_test")
        unlimited_plan_data = {
            "plan_name": unique_plan_name,
            "daily_limit": -1,
            "description": "Unlimited test plan",
            "features": ["unlimited_feature"],
        }

        create_response = client.post("/api/admin/ai-chat/plans", json=unlimited_plan_data)

        # Verify warning message is returned
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "creation ignored" in create_data["message"]
        assert create_response.status_code == 200

        # Since creation is now disabled, the plan won't actually exist
        # Verify that the original plans are still available
        get_response = client.get("/api/admin/ai-chat/plans/enterprise")
        assert get_response.status_code == 200
        plan_data = get_response.json()
        assert plan_data["daily_limit"] == -1  # Original enterprise plan

    def test_zero_limit_plan_handling(self):
        """Test handling of zero-limit plans (no access)"""
        # Create a zero-limit plan
        unique_plan_name = generate_unique_plan_name("no_access_test")
        zero_plan_data = {
            "plan_name": unique_plan_name,
            "daily_limit": 0,
            "description": "No access test plan",
            "features": [],
        }

        create_response = client.post("/api/admin/ai-chat/plans", json=zero_plan_data)
        assert create_response.status_code == 200

        # Verify warning message is returned
        create_data = create_response.json()
        assert "creation ignored" in create_data["message"]
        assert "warning" in create_data


class TestAdminAPIErrorHandling:
    """Test error handling in admin API endpoints"""

    def test_malformed_request_data(self):
        """Test handling of malformed request data"""
        # Missing required fields
        incomplete_data = {
            "plan_name": "incomplete_plan"
            # Missing daily_limit
        }

        response = client.post("/api/admin/ai-chat/plans", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_invalid_json_data(self):
        """Test handling of invalid JSON data"""
        response = client.put(
            "/api/admin/ai-chat/plans/basic",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_config_update_disabled(self):
        """Test that configuration updates are disabled"""
        update_data = {
            "plan_name": "basic",
            "daily_limit": 20,
            "description": "Should be ignored",
        }

        response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert "update ignored" in data["message"]
        assert "warning" in data

    @patch("app.config.config_manager._load_config")
    def test_config_reload_failure(self, mock_load_config):
        """Test handling of configuration reload failures"""
        # Mock the config loading to raise an exception
        mock_load_config.side_effect = Exception("Config load failed")

        response = client.get("/api/admin/ai-chat/config/reload")
        assert response.status_code == 500
        data = response.json()
        assert "Failed to reload" in data["detail"] or "Config load failed" in data["detail"]
