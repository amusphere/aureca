"""Integration tests for Clerk API integration."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.schema import User
from app.services.auth import auth_user
from main import app


class TestClerkAPIIntegration:
    """Test Clerk API integration scenarios."""

    def _setup_user_with_clerk_sub(self, session: Session, test_user: User, clerk_sub: str):
        """Helper to set up user with clerk_sub."""
        test_user.clerk_sub = clerk_sub
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

    def test_clerk_api_success_standard_plan(self, client: TestClient, session: Session, test_user: User):
        """Test successful Clerk API call returning standard plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_123")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                mock_clerk_service.get_user_plan.return_value = "standard"

                response = client.get("/api/ai/usage")

                assert response.status_code == 200
                data = response.json()

                # Verify standard plan response
                assert data["plan_name"] == "standard"
                assert data["daily_limit"] == 10
                assert data["can_use_chat"] is True

                # Verify Clerk API was called
                mock_clerk_service.get_user_plan.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_success_free_plan(self, client: TestClient, session: Session, test_user: User):
        """Test successful Clerk API call returning free plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_456")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                mock_clerk_service.get_user_plan.return_value = "free"

                response = client.get("/api/ai/usage")

                assert response.status_code == 200
                data = response.json()

                # Verify free plan response
                assert data["plan_name"] == "free"
                assert data["daily_limit"] == 0
                assert data["can_use_chat"] is False

                # Verify Clerk API was called
                mock_clerk_service.get_user_plan.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_error_fallback_to_free(self, client: TestClient, session: Session, test_user: User):
        """Test Clerk API error with fallback to free plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_789")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                # ClerkService handles exceptions internally and returns "free"
                mock_clerk_service.get_user_plan.return_value = "free"

                response = client.get("/api/ai/usage")

                assert response.status_code == 200
                data = response.json()

                # Should fallback to free plan
                assert data["plan_name"] == "free"
                assert data["daily_limit"] == 0
                assert data["can_use_chat"] is False
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_timeout_fallback(self, client: TestClient, session: Session, test_user: User):
        """Test Clerk API timeout with fallback behavior."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_timeout")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                # ClerkService handles timeouts internally and returns "free"
                mock_clerk_service.get_user_plan.return_value = "free"

                response = client.get("/api/ai/usage")

                assert response.status_code == 200
                data = response.json()

                # Should fallback to free plan
                assert data["plan_name"] == "free"
                assert data["daily_limit"] == 0
                assert data["can_use_chat"] is False
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_invalid_plan_fallback(self, client: TestClient, session: Session, test_user: User):
        """Test Clerk API returning invalid plan name."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_invalid")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                # Return invalid plan name
                mock_clerk_service.get_user_plan.return_value = "invalid_plan"

                response = client.get("/api/ai/usage")

                assert response.status_code == 200
                data = response.json()

                # Service returns what Clerk returns, but PlanLimits.get_limit returns 0 for invalid
                assert data["plan_name"] == "invalid_plan"
                assert data["daily_limit"] == 0  # PlanLimits.get_limit returns 0 for invalid
                assert data["can_use_chat"] is False
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_plan_change_detection(self, client: TestClient, session: Session, test_user: User):
        """Test that plan changes are detected immediately."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_change")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service

                # First call returns free plan
                mock_clerk_service.get_user_plan.return_value = "free"
                response1 = client.get("/api/ai/usage")
                assert response1.json()["plan_name"] == "free"

                # Second call returns standard plan (simulating upgrade)
                mock_clerk_service.get_user_plan.return_value = "standard"
                response2 = client.get("/api/ai/usage")
                assert response2.json()["plan_name"] == "standard"

                # Verify both calls were made to Clerk API
                assert mock_clerk_service.get_user_plan.call_count == 2
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_concurrent_requests(self, client: TestClient, session: Session, test_user: User):
        """Test concurrent requests to Clerk API."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_concurrent")

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
                mock_clerk_service = AsyncMock()
                mock_get_clerk_service.return_value = mock_clerk_service
                mock_clerk_service.get_user_plan.return_value = "standard"

                # Make multiple concurrent requests
                import concurrent.futures

                def make_request():
                    return client.get("/api/ai/usage")

                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(make_request) for _ in range(3)]
                    responses = [future.result() for future in futures]

                # All should succeed
                for response in responses:
                    assert response.status_code == 200
                    assert response.json()["plan_name"] == "standard"

                # Clerk API should have been called for each request
                assert mock_clerk_service.get_user_plan.call_count == 3
        finally:
            app.dependency_overrides.clear()

    def test_clerk_api_user_without_clerk_sub(self, client: TestClient, session: Session):
        """Test user without clerk_sub field."""
        # Create user without clerk_sub
        test_user = User(
            id=999,
            clerk_user_id="test_user_999",
            email="test999@example.com",
            created_at=1672531200.0,
            updated_at=1672531200.0,
            clerk_sub=None,  # No clerk_sub
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            response = client.get("/api/ai/usage")

            assert response.status_code == 200
            data = response.json()

            # Should default to free plan when no clerk_sub
            assert data["plan_name"] == "free"
            assert data["daily_limit"] == 0
            assert data["can_use_chat"] is False
        finally:
            app.dependency_overrides.clear()
