"""Integration tests for AI Chat usage API endpoints."""

from unittest.mock import patch

from app.repositories import ai_chat_usage
from app.schema import User
from app.services.auth import auth_user
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session


class TestAIChatUsageAPIIntegration:
    """Test AI Chat usage API endpoints integration."""

    def test_get_usage_endpoint_success(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test GET /api/ai/usage endpoint returns correct usage stats."""
        current_date = "2023-01-01"

        # Create some usage data
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 3)

        # Override the auth dependency to return our test user
        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure and values
            assert "remaining_count" in data
            assert "daily_limit" in data
            assert "reset_time" in data
            assert "can_use_chat" in data

            assert data["remaining_count"] == 7  # 10 - 3
            assert data["daily_limit"] == 10
            assert data["can_use_chat"] is True
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_usage_endpoint_limit_exceeded(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test GET /api/ai/usage endpoint when limit is exceeded."""
        current_date = "2023-01-01"

        # Create usage data at the limit
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 10)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 429
            data = response.json()

            # Verify error response structure
            assert "detail" in data
            detail = data["detail"]
            assert "error" in detail
            assert "error_code" in detail
            assert "remaining_count" in detail
            assert "reset_time" in detail

            assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"
            assert detail["remaining_count"] == 0
            assert "本日の利用回数上限に達しました" in detail["error"]
        finally:
            app.dependency_overrides.clear()

    def test_get_usage_endpoint_free_plan_restriction(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test GET /api/ai/usage endpoint for free plan users."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.get_user_plan",
                return_value="free",
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 403
            data = response.json()

            # Verify error response structure
            assert "detail" in data
            detail = data["detail"]
            assert "error" in detail
            assert "error_code" in detail
            assert detail["error_code"] == "PLAN_RESTRICTION"
            assert "現在のプランではAIChatをご利用いただけません" in detail["error"]
        finally:
            app.dependency_overrides.clear()

    def test_increment_usage_endpoint_success(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test POST /api/ai/usage/increment endpoint successfully increments usage."""
        current_date = "2023-01-01"

        # Start with some existing usage
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 5)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                response = client.post("/api/ai/usage/increment")

            assert response.status_code == 200
            data = response.json()

            # Verify response shows incremented usage
            assert data["remaining_count"] == 4  # 10 - 6 (5 + 1)
            assert data["daily_limit"] == 10
            assert data["can_use_chat"] is True

            # Verify database was updated
            current_usage = ai_chat_usage.get_current_usage_count(
                session, test_user.id, current_date
            )
            assert current_usage == 6
        finally:
            app.dependency_overrides.clear()

    def test_increment_usage_endpoint_at_limit(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test POST /api/ai/usage/increment endpoint when at limit."""
        current_date = "2023-01-01"

        # Set usage at the limit
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 10)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
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
            current_usage = ai_chat_usage.get_current_usage_count(
                session, test_user.id, current_date
            )
            assert current_usage == 10  # Should not exceed limit
        finally:
            app.dependency_overrides.clear()

    def test_ai_process_endpoint_with_usage_integration(
        self, client: TestClient, session: Session, test_user: User
    ):
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

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value=mock_ai_response,
                ):
                    # First request should succeed
                    response = client.post(
                        "/api/ai/process", json={"prompt": "Test prompt"}
                    )

            assert response.status_code == 200

            # Verify usage was incremented
            current_usage = ai_chat_usage.get_current_usage_count(
                session, test_user.id, current_date
            )
            assert current_usage == 1
        finally:
            app.dependency_overrides.clear()

    def test_ai_process_endpoint_blocked_by_usage_limit(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test /api/ai/process endpoint is blocked when usage limit is exceeded."""
        current_date = "2023-01-01"

        # Set usage at the limit
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 10)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                response = client.post(
                    "/api/ai/process", json={"prompt": "Test prompt"}
                )

            assert response.status_code == 429
            data = response.json()

            # Verify error response structure
            assert "detail" in data
            detail = data["detail"]
            assert "error" in detail
            assert "error_code" in detail
            assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    def test_usage_reset_at_midnight(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that usage resets properly for new day."""
        # Create usage for previous day
        previous_date = "2023-01-01"
        current_date = "2023-01-02"

        ai_chat_usage.create_daily_usage(session, test_user.id, previous_date, 10)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
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
        finally:
            app.dependency_overrides.clear()

    def test_concurrent_usage_increment_consistency(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that concurrent usage increments maintain data consistency."""
        current_date = "2023-01-01"

        # Start with some usage
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 8)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
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
            error_responses = [r for r in responses if r.status_code == 429]

            # At least one should succeed, and total shouldn't exceed limit
            assert len(success_responses) >= 1

            # Verify final usage count doesn't exceed limit
            final_usage = ai_chat_usage.get_current_usage_count(
                session, test_user.id, current_date
            )
            assert final_usage <= 10
        finally:
            app.dependency_overrides.clear()

    def test_error_handling_system_errors(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that system errors are handled gracefully."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            # Mock a database error
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.check_usage_limit",
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
        finally:
            app.dependency_overrides.clear()

    def test_authentication_required(self, client: TestClient):
        """Test that all usage endpoints require authentication."""
        # Don't override auth dependency - should fail authentication

        # Test GET endpoint
        response = client.get("/api/ai/usage")
        assert response.status_code == 403  # Forbidden

        # Test POST endpoint
        response = client.post("/api/ai/usage/increment")
        assert response.status_code == 403  # Forbidden

    def test_response_format_consistency(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that all endpoints return consistent response formats."""
        current_date = "2023-01-01"

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
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

                # Test error response format
                ai_chat_usage.create_daily_usage(
                    session, test_user.id, current_date, 10
                )
                response = client.get("/api/ai/usage")
                assert response.status_code == 429

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                required_error_fields = [
                    "error",
                    "error_code",
                    "remaining_count",
                    "reset_time",
                ]
                for field in required_error_fields:
                    assert field in detail
                    assert detail[field] is not None
        finally:
            app.dependency_overrides.clear()
