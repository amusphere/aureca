"""
AI Chat Usage Error Handling Integration Tests

Tests comprehensive error handling scenarios across the AI chat usage system,
including malformed requests, database connection errors, and AI process errors.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.schema import User
from app.services.auth import auth_user
from main import app


class TestAIChatUsageErrorHandling:
    """Test comprehensive error handling scenarios in AI chat usage system."""

    @pytest.fixture(autouse=True)
    def setup_test_dependencies(
        self,
        setup_app_overrides,
        mock_clerk_service: MagicMock,
        test_user: User,
    ):
        """Setup test dependencies using dependency overrides."""
        # Setup authentication override
        app.dependency_overrides[auth_user] = lambda: test_user

        yield {
            "mock_clerk_service": mock_clerk_service,
            "test_user": test_user,
        }

        # Cleanup
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    def test_malformed_request_handling(self, client: TestClient):
        """Test handling of malformed requests to AI chat usage endpoints."""
        # Test malformed JSON in request body for AI process endpoint
        malformed_data = '{"incomplete": "json"'  # Invalid JSON

        # Send raw malformed request
        response = client.post("/api/ai/process", content=malformed_data, headers={"Content-Type": "application/json"})

        # Should return 422 for malformed request
        assert response.status_code == 422
        assert "detail" in response.json()

    @patch("app.services.ai_chat_usage_service.AIChatUsageService.get_usage_stats")
    def test_database_connection_error_handling(self, mock_get_usage_stats, client: TestClient):
        """Test handling of database connection errors."""
        # Mock service method to raise database connection error
        mock_get_usage_stats.side_effect = OperationalError("Connection failed", orig=None, params=None)

        # Request should fail gracefully with 500 error
        response = client.get("/api/ai/usage")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    @patch("app.services.ai.core.hub.AIHub.process_request")
    def test_ai_process_error_integration(self, mock_ai_hub_process, client: TestClient):
        """Test handling of AI processing errors in integration context."""
        # Mock AI hub processing to raise an exception
        mock_ai_hub_process.side_effect = Exception("AI processing failed")

        # Request should handle AI processing errors gracefully
        response = client.post("/api/ai/process", json={"prompt": "test prompt for AI processing"})

        # Should return 500 for AI processing errors
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
