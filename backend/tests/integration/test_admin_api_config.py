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
        assert "Successfully updated" in data["message"]
        assert data["plan_name"] == "basic"
        assert data["daily_limit"] == "15"

        # Verify the update by getting the plan
        get_response = client.get("/api/admin/ai-chat/plans/basic")
        assert get_response.status_code == 200
        updated_plan = get_response.json()

        assert updated_plan["daily_limit"] == 15
        assert updated_plan["description"] == "Updated basic plan"
        assert updated_plan["features"] == ["updated_feature1", "updated_feature2"]

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
        assert "Successfully created" in data["message"]
        assert data["plan_name"] == unique_plan_name
        assert data["daily_limit"] == "25"

        # Verify the creation by getting the plan
        get_response = client.get(f"/api/admin/ai-chat/plans/{unique_plan_name}")
        assert get_response.status_code == 200
        created_plan = get_response.json()

        assert created_plan["plan_name"] == unique_plan_name
        assert created_plan["daily_limit"] == 25
        assert created_plan["description"] == "Test plan created via API"
        assert created_plan["features"] == ["test_feature1", "test_feature2"]

    def test_create_duplicate_plan(self):
        """Test creating a plan that already exists"""
        duplicate_plan_data = {
            "plan_name": "basic",  # Already exists
            "daily_limit": 20,
            "description": "Duplicate plan",
        }

        response = client.post("/api/admin/ai-chat/plans", json=duplicate_plan_data)

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

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
        assert "Configuration reloaded" in data["message"]
        assert "timestamp" in data


class TestAdminAPIIntegration:
    """Integration tests for admin API with configuration system"""

    def test_api_reflects_config_changes(self):
        """Test that API endpoints reflect configuration changes"""
        # First, get the current basic plan configuration
        initial_response = client.get("/api/admin/ai-chat/plans/basic")
        initial_data = initial_response.json()
        initial_limit = initial_data["daily_limit"]

        # Update the plan via API
        new_limit = initial_limit + 5
        update_data = {
            "plan_name": "basic",
            "daily_limit": new_limit,
            "description": "API integration test plan",
        }

        update_response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)
        assert update_response.status_code == 200

        # Verify the change is reflected in the configuration manager
        assert config_manager.get_ai_chat_plan_limit("basic") == new_limit

        # Verify the change is reflected in subsequent API calls
        updated_response = client.get("/api/admin/ai-chat/plans/basic")
        updated_data = updated_response.json()
        assert updated_data["daily_limit"] == new_limit
        assert updated_data["description"] == "API integration test plan"

        # Verify the change is reflected in the all plans endpoint
        all_plans_response = client.get("/api/admin/ai-chat/plans")
        all_plans_data = all_plans_response.json()
        assert all_plans_data["plans"]["basic"]["daily_limit"] == new_limit

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
        assert create_response.status_code == 200

        # Verify the unlimited plan
        get_response = client.get(f"/api/admin/ai-chat/plans/{unique_plan_name}")
        assert get_response.status_code == 200
        plan_data = get_response.json()

        assert plan_data["daily_limit"] == -1
        assert plan_data["description"] == "Unlimited test plan"

        # Verify it's reflected in the configuration manager
        assert config_manager.get_ai_chat_plan_limit(unique_plan_name) == -1

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

        # Verify the zero-limit plan
        get_response = client.get(f"/api/admin/ai-chat/plans/{unique_plan_name}")
        assert get_response.status_code == 200
        plan_data = get_response.json()

        assert plan_data["daily_limit"] == 0
        assert plan_data["description"] == "No access test plan"
        assert plan_data["features"] == []

        # Verify it's reflected in the configuration manager
        assert config_manager.get_ai_chat_plan_limit(unique_plan_name) == 0


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

    @patch("app.routers.api.admin.update_ai_chat_plan_limit")
    def test_config_update_failure(self, mock_update):
        """Test handling of configuration update failures"""
        # Mock the update to fail
        mock_update.return_value = False

        update_data = {
            "plan_name": "basic",
            "daily_limit": 20,
            "description": "Should fail",
        }

        response = client.put("/api/admin/ai-chat/plans/basic", json=update_data)
        assert response.status_code == 500
        data = response.json()
        assert "Failed to update" in data["detail"]

    @patch("app.config.config_manager._check_file_updates")
    def test_config_reload_failure(self, mock_reload):
        """Test handling of configuration reload failures"""
        # Mock the reload to raise an exception
        mock_reload.side_effect = Exception("Reload failed")

        response = client.get("/api/admin/ai-chat/config/reload")
        assert response.status_code == 500
        data = response.json()
        assert "Failed to reload" in data["detail"]
