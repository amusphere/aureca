"""End-to-end integration tests for AI Chat usage limits feature."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database import get_session
from app.repositories import ai_chat_usage
from app.schema import User
from app.services.auth import auth_user
from main import app


class TestAIChatUsageE2EIntegration:
    """Test complete end-to-end scenarios for AI Chat usage limits."""

    @pytest.fixture(autouse=True)
    def mock_config_values(self):
        """Mock config values to ensure consistent test behavior."""
        with patch("app.services.ai_chat_usage_service.get_ai_chat_plan_limit") as mock_get_limit:

            def get_limit_side_effect(plan_name):
                limits = {
                    "free": 0,
                    "basic": 10,
                    "premium": 50,
                    "enterprise": -1,
                }
                return limits.get(plan_name, 0)

            mock_get_limit.side_effect = get_limit_side_effect
            yield

    def _setup_auth(self, test_user: User):
        """Helper to setup authentication override."""

        def get_test_user():
            return test_user

        # Store existing overrides to preserve database session override
        existing_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[auth_user] = get_test_user

        # Ensure database session override is preserved
        if get_session not in app.dependency_overrides and get_session in existing_overrides:
            app.dependency_overrides[get_session] = existing_overrides[get_session]

    def _cleanup_auth(self):
        """Helper to cleanup authentication override while preserving session override."""
        # Remove only the auth override, keep session override
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    def test_complete_user_journey_within_limits(self, client: TestClient, session: Session, test_user: User):
        """Test complete user journey from checking usage to using AI chat within limits."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Step 1: User checks initial usage
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                initial_data = response.json()
                assert initial_data["remaining_count"] == 10
                assert initial_data["daily_limit"] == 10
                assert initial_data["can_use_chat"] is True

                # Step 2: User uses AI chat (mock successful processing)
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "Test summary"},
                        "error": None,
                    },
                ):
                    ai_response = client.post("/api/ai/process", json={"prompt": "Test prompt"})
                    assert ai_response.status_code == 200

                # Step 3: Check usage after AI processing
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                updated_data = response.json()
                assert updated_data["remaining_count"] == 9  # Decremented by 1
                assert updated_data["daily_limit"] == 10
                assert updated_data["can_use_chat"] is True

                # Verify database state
                current_usage = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
                assert current_usage == 1
        finally:
            self._cleanup_auth()

    def test_complete_user_journey_reaching_limit(self, client: TestClient, session: Session, test_user: User):
        """Test complete user journey when reaching usage limit."""
        current_date = "2023-01-01"

        # Set user close to limit
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 9)

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Step 1: Check usage near limit
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 1
                assert data["can_use_chat"] is True

                # Step 2: Use last available AI chat
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "Final summary"},
                        "error": None,
                    },
                ):
                    ai_response = client.post("/api/ai/process", json={"prompt": "Final prompt"})
                    assert ai_response.status_code == 200

                # Step 3: Check usage after reaching limit
                response = client.get("/api/ai/usage")
                assert response.status_code == 429

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"
                assert detail["remaining_count"] == 0
                assert "本日の利用回数上限に達しました" in detail["error"]

                # Step 4: Attempt to use AI chat when at limit
                ai_response = client.post("/api/ai/process", json={"prompt": "Should fail"})
                assert ai_response.status_code == 429

                # Verify database state
                final_usage = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
                assert final_usage == 10  # At limit
        finally:
            self._cleanup_auth()

    def test_daily_reset_user_journey(self, client: TestClient, session: Session, test_user: User):
        """Test user journey across daily reset boundary."""
        day1_date = "2023-01-01"
        day2_date = "2023-01-02"

        # Day 1: Use up all quota
        ai_chat_usage.create_daily_usage(session, test_user.id, day1_date, 10)

        self._setup_auth(test_user)

        try:
            # Check Day 1 - should be at limit
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=day1_date,
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 429

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["remaining_count"] == 0

            # Day 2 - should reset
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=day2_date,
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 10  # Full quota restored
                assert data["can_use_chat"] is True

                # Should be able to use AI chat again
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "New day response"},
                        "error": None,
                    },
                ):
                    ai_response = client.post("/api/ai/process", json={"prompt": "New day prompt"})
                    assert ai_response.status_code == 200
        finally:
            self._cleanup_auth()

    def test_free_plan_user_complete_journey(self, client: TestClient, test_user: User):
        """Test complete journey for free plan user (should be blocked)."""
        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.get_user_plan",
                return_value="free",
            ):
                # Step 1: Check usage - should be blocked
                response = client.get("/api/ai/usage")
                assert response.status_code == 403

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["error_code"] == "PLAN_RESTRICTION"
                assert "現在のプランではAIChatをご利用いただけません" in detail["error"]

                # Step 2: Attempt AI chat - should be blocked
                ai_response = client.post("/api/ai/process", json={"prompt": "Should be blocked"})
                assert ai_response.status_code == 403

                # Step 3: Attempt increment - should be blocked
                increment_response = client.post("/api/ai/usage/increment")
                assert increment_response.status_code == 403
        finally:
            self._cleanup_auth()

    def test_concurrent_users_isolation(self, client: TestClient, session: Session):
        """Test that usage limits are properly isolated between users."""
        # Create two test users
        user1 = User(
            id=1,
            clerk_user_id="user1_123",
            email="user1@example.com",
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        user2 = User(
            id=2,
            clerk_user_id="user2_123",
            email="user2@example.com",
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        current_date = "2023-01-01"

        # User1 uses up their quota
        ai_chat_usage.create_daily_usage(session, user1.id, current_date, 10)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # User1 should be at limit
                self._setup_auth(user1)
                response = client.get("/api/ai/usage")
                assert response.status_code == 429

                # User2 should have full quota
                self._setup_auth(user2)
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 10
                assert data["can_use_chat"] is True

                # User2 should be able to use AI chat
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "User2 response"},
                        "error": None,
                    },
                ):
                    ai_response = client.post("/api/ai/process", json={"prompt": "User2 prompt"})
                    assert ai_response.status_code == 200
        finally:
            self._cleanup_auth()

    def test_error_recovery_user_journey(self, client: TestClient, session: Session, test_user: User):
        """Test user journey with temporary errors and recovery."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Step 1: Normal usage check
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                # Step 2: Simulate temporary database error
                with patch(
                    "app.repositories.ai_chat_usage.get_current_usage_count",
                    side_effect=Exception("DB error"),
                ):
                    error_response = client.get("/api/ai/usage")
                    assert error_response.status_code == 500

                    error_data = error_response.json()
                    assert "detail" in error_data
                    detail = error_data["detail"]
                    assert detail["error_code"] == "SYSTEM_ERROR"

                # Step 3: System recovers
                recovery_response = client.get("/api/ai/usage")
                assert recovery_response.status_code == 200

                data = recovery_response.json()
                assert data["remaining_count"] == 10
                assert data["can_use_chat"] is True
        finally:
            self._cleanup_auth()

    def test_api_consistency_across_endpoints(self, client: TestClient, session: Session, test_user: User):
        """Test that all API endpoints return consistent data formats."""
        current_date = "2023-01-01"

        # Create some usage
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 3)

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Test GET /api/ai/usage
                get_response = client.get("/api/ai/usage")
                assert get_response.status_code == 200
                get_data = get_response.json()

                # Test POST /api/ai/usage/increment
                increment_response = client.post("/api/ai/usage/increment")
                assert increment_response.status_code == 200
                increment_data = increment_response.json()

                # Both should have same structure
                required_fields = [
                    "remaining_count",
                    "daily_limit",
                    "reset_time",
                    "can_use_chat",
                ]
                for field in required_fields:
                    assert field in get_data
                    assert field in increment_data

                # Increment should show updated count
                assert increment_data["remaining_count"] == get_data["remaining_count"] - 1
        finally:
            self._cleanup_auth()

    def test_high_usage_scenario(self, client: TestClient, session: Session, test_user: User):
        """Test scenario with high usage approaching limit."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "Test summary"},
                        "error": None,
                    },
                ):
                    # Use AI chat 9 times (approaching limit)
                    for i in range(9):
                        response = client.post("/api/ai/process", json={"prompt": f"Prompt {i + 1}"})
                        assert response.status_code == 200

                        # Check remaining count
                        usage_response = client.get("/api/ai/usage")
                        assert usage_response.status_code == 200

                        data = usage_response.json()
                        assert data["remaining_count"] == 10 - (i + 1)
                        assert data["can_use_chat"] is True

                    # 10th request should succeed but reach limit
                    final_response = client.post("/api/ai/process", json={"prompt": "Final prompt"})
                    assert final_response.status_code == 200

                    # Now should be at limit
                    limit_response = client.get("/api/ai/usage")
                    assert limit_response.status_code == 429

                    # 11th request should fail
                    over_limit_response = client.post("/api/ai/process", json={"prompt": "Over limit"})
                    assert over_limit_response.status_code == 429
        finally:
            self._cleanup_auth()

    def test_usage_tracking_accuracy(self, client: TestClient, session: Session, test_user: User):
        """Test that usage tracking is accurate across multiple operations."""
        current_date = "2023-01-01"

        self._setup_auth(test_user)

        try:
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
                db_usage = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
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
                final_db_usage = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
                assert final_db_usage == 2
        finally:
            self._cleanup_auth()
