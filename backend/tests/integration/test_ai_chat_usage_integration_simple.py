"""Simplified integration tests for AI Chat usage limits feature."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import User
from app.services.auth import auth_user
from main import app


class TestAIChatUsageIntegrationSimple:
    """Test AI Chat usage integration with simplified approach."""

    @pytest.fixture(autouse=True)
    def setup_test_dependencies(
        self,
        setup_app_overrides,
        mock_clerk_service: MagicMock,
        test_user: User,
    ):
        """Setup test dependencies using dependency overrides."""
        # Mock PlanLimits.get_limit
        with patch("app.services.ai_chat_usage_service.PlanLimits.get_limit") as mock_get_limit:

            def get_limit_side_effect(plan_name):
                limits = {
                    "free": 0,
                    "standard": 10,
                }
                return limits.get(plan_name, 0)

            mock_get_limit.side_effect = get_limit_side_effect

            # Setup authentication override
            app.dependency_overrides[auth_user] = lambda: test_user

            yield {
                "mock_get_limit": mock_get_limit,
                "mock_clerk_service": mock_clerk_service,
            }

    def test_usage_endpoint_success_flow(self, client: TestClient, session: Session, test_user: User):
        """Test successful usage check flow."""
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

    def test_usage_increment_success_flow(self, client: TestClient, session: Session, test_user: User):
        """Test successful usage increment flow."""
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

    def test_usage_limit_exceeded_flow(self, client: TestClient, session: Session, test_user: User):
        """Test usage limit exceeded flow."""
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
        assert data["can_use_chat"] is False
        assert data["current_usage"] == 10

    @pytest.mark.skip(reason="Skipped due to temporary workaround: all users treated as standard plan")
    def test_free_plan_restriction_flow(self, client: TestClient, test_user: User, setup_test_dependencies):
        """Test free plan restriction flow."""
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

    def test_daily_reset_flow(self, client: TestClient, session: Session, test_user: User):
        """Test daily reset flow."""
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

    def test_authentication_required_flow(self, session: Session):
        """Test that authentication is required."""
        # Create a client without auth override but with test database
        from fastapi.testclient import TestClient

        from app.database import get_session
        from main import app

        def get_session_override():
            return session

        # Create a new app instance with only database override, no auth override
        test_app = app
        test_app.dependency_overrides.clear()
        test_app.dependency_overrides[get_session] = get_session_override

        with TestClient(test_app) as client_no_auth:
            # Test GET endpoint
            response = client_no_auth.get("/api/ai/usage")
            assert response.status_code in [
                401,
                403,
            ]  # Either is acceptable for auth failure

            # Test POST endpoint
            response = client_no_auth.post("/api/ai/usage/increment")
            assert response.status_code in [
                401,
                403,
            ]  # Either is acceptable for auth failure

    def test_system_error_handling_flow(self, client: TestClient, test_user: User):
        """Test system error handling flow."""
        # Mock a database error in the service method that's actually called
        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService.get_usage_stats",
            side_effect=Exception("Database error"),
        ):
            response = client.get("/api/ai/usage")

        assert response.status_code == 500
        data = response.json()

        # Error responses are wrapped in detail field
        assert "detail" in data
        detail = data["detail"]

        assert "error_code" in detail
        assert detail["error_code"] == "SYSTEM_ERROR"

    def test_usage_tracking_accuracy_flow(self, client: TestClient, session: Session, test_user: User):
        """Test that usage tracking is accurate across multiple operations."""
        current_date = "2023-01-01"

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            # Initial state
            response = client.get("/api/ai/usage")
            assert response.status_code == 200
            assert response.json()["remaining_count"] == 10

            # Manual increment
            increment_response = client.post("/api/ai/usage/increment")
            assert increment_response.status_code == 200
            assert increment_response.json()["remaining_count"] == 9

            # Verify database consistency
            db_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            assert db_usage == 1

            # Another increment
            increment_response2 = client.post("/api/ai/usage/increment")
            assert increment_response2.status_code == 200
            assert increment_response2.json()["remaining_count"] == 8

            # Final verification
            final_response = client.get("/api/ai/usage")
            assert final_response.status_code == 200
            assert final_response.json()["remaining_count"] == 8

            # Database should match
            final_db_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            assert final_db_usage == 2

    def test_response_format_consistency_flow(self, client: TestClient, session: Session, test_user: User):
        """Test that response formats are consistent."""
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

    def test_concurrent_users_isolation_flow(self, client: TestClient, session: Session):
        """Test that usage limits are properly isolated between users."""
        from tests.utils.test_data_factory import TestDataFactory

        # Create two test users using factory with unique IDs
        user1 = TestDataFactory.create_user(
            id=101,  # Use unique ID to avoid conflicts
            clerk_sub="user1_123",
            email="user1@example.com",
        )
        user2 = TestDataFactory.create_user(
            id=102,  # Use unique ID to avoid conflicts
            clerk_sub="user2_123",
            email="user2@example.com",
        )
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        current_date = "2023-01-01"

        # User1 uses up their quota
        AIChatUsageRepository.create_daily_usage(session, user1.id, current_date, 10)

        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=current_date,
        ):
            # Test User1 - should be at limit
            app.dependency_overrides[auth_user] = lambda: user1
            response = client.get("/api/ai/usage")
            assert response.status_code == 200
            assert response.json()["can_use_chat"] is False

            # Test User2 - should have full quota
            app.dependency_overrides[auth_user] = lambda: user2
            response = client.get("/api/ai/usage")
            assert response.status_code == 200

            data = response.json()
            assert data["remaining_count"] == 10
            assert data["can_use_chat"] is True
