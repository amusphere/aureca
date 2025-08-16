"""Integration tests for AI Chat usage API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import User
from app.services.auth import auth_user
from main import app


class TestAIChatUsageAPIIntegration:
    """Test AI Chat usage API endpoints integration."""

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
        }

    def test_get_usage_endpoint_success(self, client: TestClient, session: Session, test_user: User):
        """Test GET /api/ai/usage endpoint returns correct usage stats."""
        current_date = "2023-01-01"

        # Create some usage data
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 3)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure and values (updated for new API)
        assert "remaining_count" in data
        assert "daily_limit" in data
        assert "current_usage" in data
        assert "plan_name" in data
        assert "reset_time" in data
        assert "can_use_chat" in data

        assert data["remaining_count"] == 7  # 10 - 3
        assert data["daily_limit"] == 10
        assert data["current_usage"] == 3
        assert data["plan_name"] == "standard"
        assert data["can_use_chat"] is True

    def test_get_usage_endpoint_limit_exceeded(self, client: TestClient, session: Session, test_user: User):
        """Test GET /api/ai/usage endpoint when limit is exceeded."""
        current_date = "2023-01-01"

        # Create usage data at the limit
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 10)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.get("/api/ai/usage")

        # Usage endpoint now returns 200 with usage stats, not 429
        assert response.status_code == 200
        data = response.json()

        # Verify response shows limit exceeded state
        assert data["remaining_count"] == 0
        assert data["daily_limit"] == 10
        assert data["current_usage"] == 10
        assert data["can_use_chat"] is False

    @pytest.mark.skip(reason="Skipped due to temporary workaround: all users treated as standard plan")
    def test_get_usage_endpoint_free_plan_restriction(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test GET /api/ai/usage endpoint for free plan users."""
        # Mock ClerkService to return free plan
        setup_test_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

        response = client.get("/api/ai/usage")

        # Usage endpoint now returns 200 with free plan stats
        assert response.status_code == 200
        data = response.json()

        # Verify free plan response
        assert data["remaining_count"] == 0
        assert data["daily_limit"] == 0
        assert data["plan_name"] == "free"
        assert data["can_use_chat"] is False

    def test_increment_usage_endpoint_success(self, client: TestClient, session: Session, test_user: User):
        """Test POST /api/ai/usage/increment endpoint successfully increments usage."""
        current_date = "2023-01-01"

        # Start with some existing usage
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 5)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.post("/api/ai/usage/increment")

        assert response.status_code == 200
        data = response.json()

        # Verify response shows incremented usage (updated for new API)
        assert data["remaining_count"] == 4  # 10 - 6 (5 + 1)
        assert data["daily_limit"] == 10
        assert data["current_usage"] == 6
        assert data["plan_name"] == "standard"
        assert data["can_use_chat"] is True

        # Verify database was updated
        current_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
        assert current_usage == 6

    @pytest.mark.skip(reason="Skipped due to temporary workaround: usage limits not enforced")
    def test_increment_usage_endpoint_at_limit(self, client: TestClient, session: Session, test_user: User):
        """Test POST /api/ai/usage/increment endpoint when at limit."""
        current_date = "2023-01-01"

        # Set usage at the limit
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 10)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.post("/api/ai/usage/increment")

        assert response.status_code == 429
        data = response.json()

        # Verify error response
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"
        assert detail["remaining_count"] == 0

        # Verify database was not incremented beyond limit
        current_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
        assert current_usage == 10  # Should not exceed limit

    def test_ai_process_endpoint_with_usage_integration(self, client: TestClient, session: Session, test_user: User):
        """Test /api/ai/process endpoint integrates with usage limits."""
        current_date = "2023-01-01"

        # Mock the AI processing to avoid actual LLM calls
        mock_ai_response = {
            "success": True,
            "operator_response": None,
            "execution_results": [],
            "summary": {"message": "Test summary"},
            "error": None,
        }

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            with patch(
                "app.services.ai.AIHub.process_request",
                return_value=mock_ai_response,
            ):
                # First request should succeed
                response = client.post("/api/ai/process", json={"prompt": "Test prompt"})

        assert response.status_code == 200

        # Verify usage was incremented
        current_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
        assert current_usage == 1

    @pytest.mark.skip(reason="Skipped due to temporary workaround: usage limits not enforced")
    def test_ai_process_endpoint_blocked_by_usage_limit(self, client: TestClient, session: Session, test_user: User):
        """Test /api/ai/process endpoint is blocked when usage limit is exceeded."""
        current_date = "2023-01-01"

        # Set usage at the limit
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 10)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.post("/api/ai/process", json={"prompt": "Test prompt"})

        assert response.status_code == 429
        data = response.json()

        # Verify error response structure
        assert "detail" in data
        detail = data["detail"]
        assert "error" in detail
        assert "error_code" in detail
        assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"

    def test_usage_reset_at_midnight(self, client: TestClient, session: Session, test_user: User):
        """Test that usage resets properly for new day."""
        # Create usage for previous day
        previous_date = "2023-01-01"
        current_date = "2023-01-02"

        AIChatUsageRepository.create_daily_usage(session, test_user.id, previous_date, 10)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Should have full limit available for new day
        assert data["remaining_count"] == 10
        assert data["can_use_chat"] is True

    def test_concurrent_usage_increment_consistency(self, client: TestClient, session: Session, test_user: User):
        """Test that concurrent usage increments maintain data consistency."""
        current_date = "2023-01-01"

        # Start with some usage
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 8)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            # Simulate two concurrent increment requests
            response1 = client.post("/api/ai/usage/increment")
            response2 = client.post("/api/ai/usage/increment")

        # In a test environment without proper database locking,
        # both requests might succeed. Check the final state instead.
        responses = [response1, response2]
        success_responses = [r for r in responses if r.status_code == 200]
        # error_responses = [r for r in responses if r.status_code == 429]  # Unused for now

        # At least one should succeed, and total shouldn't exceed limit
        assert len(success_responses) >= 1

        # Verify final usage count doesn't exceed limit
        final_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
        assert final_usage <= 10

    def test_error_handling_system_errors(self, client: TestClient, session: Session, test_user: User):
        """Test that system errors are handled gracefully."""
        # Mock a database error
        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService.get_usage_stats",
            side_effect=Exception("Database error"),
        ):
            response = client.get("/api/ai/usage")

        assert response.status_code == 500
        data = response.json()

        # Verify error response structure
        assert "detail" in data
        detail = data["detail"]
        assert "error" in detail
        assert "error_code" in detail
        assert detail["error_code"] == "SYSTEM_ERROR"
        assert "一時的なエラーが発生しました" in detail["error"]

    def test_authentication_required(self):
        """Test that all usage endpoints require authentication."""
        # Create a client without auth override
        from fastapi.testclient import TestClient

        from main import app

        # Clear all dependency overrides to test unauthenticated access
        original_overrides = app.dependency_overrides.copy()
        app.dependency_overrides.clear()

        try:
            with TestClient(app) as client_no_auth:
                # Test GET endpoint
                response = client_no_auth.get("/api/ai/usage")
                assert response.status_code == 403  # Forbidden

                # Test POST endpoint
                response = client_no_auth.post("/api/ai/usage/increment")
                assert response.status_code == 403  # Forbidden
        finally:
            # Restore original overrides
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)

    def test_response_format_consistency(self, client: TestClient, session: Session, test_user: User):
        """Test that all endpoints return consistent response formats."""
        current_date = "2023-01-01"

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            # Test successful response format
            response = client.get("/api/ai/usage")
            assert response.status_code == 200

            data = response.json()
            required_fields = [
                "remaining_count",
                "daily_limit",
                "reset_time",
                "can_use_chat",
            ]
            for field in required_fields:
                assert field in data
                assert data[field] is not None

            # Test at-limit response format
            AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 10)
            response = client.get("/api/ai/usage")
            assert response.status_code == 200

            limit_data = response.json()
            # At limit, should still return usage stats but with can_use_chat=False
            assert limit_data["remaining_count"] == 0
            assert limit_data["can_use_chat"] is False
            assert limit_data["daily_limit"] == 10
