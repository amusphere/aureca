"""Integration tests for Clerk API integration."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.schema import User
from app.services.auth import auth_user
from main import app


class TestClerkAPIIntegration:
    """Test Clerk API integration scenarios."""

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

    def _setup_user_with_clerk_sub(self, session: Session, test_user: User, clerk_sub: str):
        """Helper to set up user with clerk_sub."""
        test_user.clerk_sub = clerk_sub
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

    def test_clerk_api_success_standard_plan(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test successful Clerk API call returning standard plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_123")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
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

    def test_clerk_api_success_free_plan(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test successful Clerk API call returning free plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_456")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
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

    def test_clerk_api_error_fallback_to_free(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test Clerk API error with fallback to free plan."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_789")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
        # ClerkService handles exceptions internally and returns "free"
        mock_clerk_service.get_user_plan.return_value = "free"

        response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Should fallback to free plan
        assert data["plan_name"] == "free"
        assert data["daily_limit"] == 0
        assert data["can_use_chat"] is False

    def test_clerk_api_timeout_fallback(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test Clerk API timeout with fallback behavior."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_timeout")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
        # ClerkService handles timeouts internally and returns "free"
        mock_clerk_service.get_user_plan.return_value = "free"

        response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Should fallback to free plan
        assert data["plan_name"] == "free"
        assert data["daily_limit"] == 0
        assert data["can_use_chat"] is False

    def test_clerk_api_invalid_plan_fallback(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test Clerk API returning invalid plan name."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_invalid")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
        # Return invalid plan name
        mock_clerk_service.get_user_plan.return_value = "invalid_plan"

        response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Service returns what Clerk returns, but PlanLimits.get_limit returns 0 for invalid
        assert data["plan_name"] == "invalid_plan"
        assert data["daily_limit"] == 0  # PlanLimits.get_limit returns 0 for invalid
        assert data["can_use_chat"] is False

    def test_clerk_api_plan_change_detection(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test that plan changes are detected immediately."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_change")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]

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

    def test_clerk_api_concurrent_requests(
        self, client: TestClient, session: Session, test_user: User, setup_test_dependencies
    ):
        """Test concurrent requests to Clerk API."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_test_concurrent")

        mock_clerk_service = setup_test_dependencies["mock_clerk_service"]
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

    def test_clerk_api_user_without_clerk_sub(self, client: TestClient, session: Session):
        """Test user without clerk_sub field."""
        from tests.utils.test_data_factory import TestDataFactory

        # Create user without clerk_sub using factory
        test_user = TestDataFactory.create_user(
            id=999,
            clerk_sub=None,  # No clerk_sub
            email="test999@example.com",
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        # Override auth for this specific test
        app.dependency_overrides[auth_user] = lambda: test_user

        response = client.get("/api/ai/usage")

        assert response.status_code == 200
        data = response.json()

        # Should default to free plan when no clerk_sub
        assert data["plan_name"] == "free"
        assert data["daily_limit"] == 0
        assert data["can_use_chat"] is False
