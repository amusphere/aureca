"""Integration tests for AI Chat usage error handling across the system."""

from unittest.mock import patch

from app.repositories import ai_chat_usage
from app.schema import User
from app.services.ai_chat_usage_service import AIChatUsageService
from app.services.auth import auth_user
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session


class TestAIChatUsageErrorHandlingIntegration:
    """Test comprehensive error handling for AI Chat usage system."""

    def _setup_auth(self, test_user: User):
        """Helper to setup authentication override."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

    def _cleanup_auth(self):
        """Helper to cleanup authentication override."""
        app.dependency_overrides.clear()

    def test_database_connection_error_handling(
        self, client: TestClient, test_user: User
    ):
        """Test handling of database connection errors."""
        self._setup_auth(test_user)

        try:
            # Mock database connection failure
            with patch(
                "app.repositories.ai_chat_usage.get_current_usage_count",
                side_effect=Exception("Database connection failed"),
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 500
            data = response.json()

            # Verify error response structure
            assert "error" in data
            assert "error_code" in data
            assert "remaining_count" in data
            assert "reset_time" in data

            assert data["error_code"] == "SYSTEM_ERROR"
            assert "一時的なエラーが発生しました" in data["error"]
            assert data["remaining_count"] == 0
        finally:
            self._cleanup_auth()

    def test_service_layer_exception_propagation(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that service layer exceptions are properly propagated."""
        self._setup_auth(test_user)

        try:
            # Mock service layer failure
            with patch.object(
                AIChatUsageService,
                "check_usage_limit",
                side_effect=ValueError("Invalid user plan"),
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "SYSTEM_ERROR"
        finally:
            self._cleanup_auth()

    def test_repository_layer_transaction_rollback(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that repository layer handles transaction rollbacks properly."""
        current_date = "2023-01-01"

        # Create initial usage
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 5)

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Mock a failure during increment that should rollback
                with patch(
                    "app.repositories.ai_chat_usage.increment_daily_usage",
                    side_effect=Exception("Database write failed"),
                ):
                    response = client.post("/api/ai/usage/increment")

            assert response.status_code == 500

            # Verify original usage count is unchanged (transaction rolled back)
            final_usage = ai_chat_usage.get_current_usage_count(
                session, test_user.id, current_date
            )
            assert final_usage == 5  # Should remain unchanged
        finally:
            self._cleanup_auth()

    def test_authentication_failure_error_handling(self, client: TestClient):
        """Test error handling when authentication fails."""
        # Don't setup auth override - should fail authentication
        response = client.get("/api/ai/usage")

        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_malformed_request_handling(self, client: TestClient, test_user: User):
        """Test handling of malformed requests."""
        self._setup_auth(test_user)

        try:
            # Test with invalid JSON for POST endpoint
            response = client.post(
                "/api/ai/usage/increment",
                data="invalid json",
                headers={"Content-Type": "application/json"},
            )

            # Should handle malformed request gracefully
            assert response.status_code in [400, 422, 500]
        finally:
            self._cleanup_auth()

    def test_concurrent_error_scenarios(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test error handling under concurrent access scenarios."""
        current_date = "2023-01-01"

        # Set usage near limit
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 9)

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Simulate race condition where one request succeeds, another fails
                response1 = client.post("/api/ai/usage/increment")
                response2 = client.post("/api/ai/usage/increment")

            # One should succeed (reaching limit), one should fail
            statuses = [response1.status_code, response2.status_code]
            assert 200 in statuses  # One succeeds
            assert 429 in statuses  # One hits limit
        finally:
            self._cleanup_auth()

    def test_error_message_localization(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that error messages are properly localized in Japanese."""
        current_date = "2023-01-01"

        # Test usage limit exceeded error
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 10)

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 429
            data = response.json()

            # Verify Japanese error message
            assert "本日の利用回数上限に達しました" in data["error"]
            assert "明日の00:00にリセットされます" in data["error"]
        finally:
            self._cleanup_auth()

    def test_plan_restriction_error_consistency(
        self, client: TestClient, test_user: User
    ):
        """Test that plan restriction errors are consistent across endpoints."""
        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.get_user_plan",
                return_value="free",
            ):
                # Test GET endpoint
                get_response = client.get("/api/ai/usage")
                assert get_response.status_code == 403
                get_data = get_response.json()

                # Test POST endpoint
                post_response = client.post("/api/ai/usage/increment")
                assert post_response.status_code == 403
                post_data = post_response.json()

                # Both should have consistent error structure
                assert (
                    get_data["error_code"]
                    == post_data["error_code"]
                    == "PLAN_RESTRICTION"
                )
                assert (
                    "現在のプランではAIChatをご利用いただけません" in get_data["error"]
                )
                assert (
                    "現在のプランではAIChatをご利用いただけません" in post_data["error"]
                )
        finally:
            self._cleanup_auth()

    def test_reset_time_calculation_errors(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test error handling when reset time calculation fails."""
        self._setup_auth(test_user)

        try:
            # Mock reset time calculation failure
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_reset_time",
                side_effect=Exception("Timezone error"),
            ):
                response = client.get("/api/ai/usage")

            assert response.status_code == 500
            data = response.json()

            # Should still provide a reset_time field even if calculation fails
            assert "reset_time" in data
            assert data["error_code"] == "SYSTEM_ERROR"
        finally:
            self._cleanup_auth()

    def test_ai_process_error_integration(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test error handling integration with AI process endpoint."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Test usage limit check failure in AI process
                ai_chat_usage.create_daily_usage(
                    session, test_user.id, current_date, 10
                )

                response = client.post(
                    "/api/ai/process", json={"prompt": "Test prompt"}
                )

                assert response.status_code == 429
                data = response.json()
                assert data["error_code"] == "USAGE_LIMIT_EXCEEDED"

                # Verify AI processing was not attempted
                # (usage count should remain at 10, not incremented)
                final_usage = ai_chat_usage.get_current_usage_count(
                    session, test_user.id, current_date
                )
                assert final_usage == 10
        finally:
            self._cleanup_auth()

    def test_partial_failure_recovery(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test system recovery from partial failures."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # First request should succeed
                response1 = client.get("/api/ai/usage")
                assert response1.status_code == 200

                # Simulate temporary database issue
                with patch(
                    "app.repositories.ai_chat_usage.get_current_usage_count",
                    side_effect=Exception("Temporary DB error"),
                ):
                    response2 = client.get("/api/ai/usage")
                    assert response2.status_code == 500

                # System should recover after temporary issue
                response3 = client.get("/api/ai/usage")
                assert response3.status_code == 200
        finally:
            self._cleanup_auth()

    def test_graceful_degradation(
        self, client: TestClient, session: Session, test_user: User
    ):
        """Test that system degrades gracefully under various failure conditions."""
        self._setup_auth(test_user)

        try:
            # Test with various service failures
            failure_scenarios = [
                ("Database timeout", Exception("Database timeout")),
                ("Memory error", MemoryError("Out of memory")),
                ("Network error", ConnectionError("Network unreachable")),
            ]

            for scenario_name, exception in failure_scenarios:
                with patch(
                    "app.services.ai_chat_usage_service.AIChatUsageService.check_usage_limit",
                    side_effect=exception,
                ):
                    response = client.get("/api/ai/usage")

                    # Should always return a valid error response
                    assert response.status_code == 500
                    data = response.json()

                    # Should have consistent error structure
                    required_fields = [
                        "error",
                        "error_code",
                        "remaining_count",
                        "reset_time",
                    ]
                    for field in required_fields:
                        assert (
                            field in data
                        ), f"Missing {field} in response for {scenario_name}"

                    assert data["error_code"] == "SYSTEM_ERROR"
        finally:
            self._cleanup_auth()

    def test_error_response_structure_consistency(
        self, client: TestClient, test_user: User
    ):
        """Test that all error responses have consistent structure."""
        self._setup_auth(test_user)

        try:
            # Test different error types
            error_scenarios = [
                # System error
                (
                    patch(
                        "app.services.ai_chat_usage_service.AIChatUsageService.check_usage_limit",
                        side_effect=Exception("Test error"),
                    ),
                    500,
                    "SYSTEM_ERROR",
                ),
                # Plan restriction
                (
                    patch(
                        "app.services.ai_chat_usage_service.AIChatUsageService.get_user_plan",
                        return_value="free",
                    ),
                    403,
                    "PLAN_RESTRICTION",
                ),
            ]

            for mock_context, expected_status, expected_error_code in error_scenarios:
                with mock_context:
                    response = client.get("/api/ai/usage")

                    assert response.status_code == expected_status
                    data = response.json()

                    # All error responses should have these fields
                    required_fields = [
                        "error",
                        "error_code",
                        "remaining_count",
                        "reset_time",
                    ]
                    for field in required_fields:
                        assert field in data
                        assert data[field] is not None

                    assert data["error_code"] == expected_error_code
        finally:
            self._cleanup_auth()
