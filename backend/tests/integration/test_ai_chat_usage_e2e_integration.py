"""End-to-end integration tests for AI Chat usage limits feature."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import User
from app.services.auth import auth_user
from main import app


class TestAIChatUsageE2EIntegration:
    """Test complete end-to-end scenarios for AI Chat usage limits."""

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

    def test_complete_user_journey_within_limits(self, client: TestClient, session: Session, test_user: User):
        """Test complete user journey from checking usage to using AI chat within limits."""
        current_date = "2023-01-01"

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
            assert initial_data["current_usage"] == 0
            assert initial_data["plan_name"] == "standard"
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
            assert updated_data["current_usage"] == 1
            assert updated_data["can_use_chat"] is True

            # Verify database state
            current_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            assert current_usage == 1

    def test_complete_user_journey_reaching_limit(self, client: TestClient, session: Session, test_user: User):
        """Test complete user journey when reaching usage limit."""
        current_date = "2023-01-01"

        # Set user close to limit
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 9)

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
            assert response.status_code == 200

            limit_data = response.json()
            assert limit_data["remaining_count"] == 0
            assert limit_data["can_use_chat"] is False
            assert limit_data["current_usage"] == 10

            # Step 4: Attempt to use AI chat when at limit
            ai_response = client.post("/api/ai/process", json={"prompt": "Should fail"})
            assert ai_response.status_code == 429

            # Verify database state
            final_usage = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            assert final_usage == 10  # At limit

    def test_daily_reset_user_journey(self, client: TestClient, session: Session, test_user: User):
        """Test user journey across daily reset boundary."""
        day1_date = "2023-01-01"
        day2_date = "2023-01-02"

        # Day 1: Use up all quota
        AIChatUsageRepository.create_daily_usage(session, test_user.id, day1_date, 10)

        # Check Day 1 - should be at limit
        with patch(
            "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
            return_value=day1_date,
        ):
            response = client.get("/api/ai/usage")
            assert response.status_code == 200

            limit_data = response.json()
            assert limit_data["remaining_count"] == 0
            assert limit_data["can_use_chat"] is False

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

    def test_free_plan_user_complete_journey(self, client: TestClient, test_user: User, setup_test_dependencies):
        """Test complete journey for free plan user (should be blocked)."""
        # Mock ClerkService to return free plan
        setup_test_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

        # Step 1: Check usage - should show free plan limits
        response = client.get("/api/ai/usage")
        assert response.status_code == 200

        data = response.json()
        assert data["daily_limit"] == 0
        assert data["remaining_count"] == 0
        assert data["plan_name"] == "free"
        assert data["can_use_chat"] is False

        # Step 2: Attempt AI chat - should be blocked
        ai_response = client.post("/api/ai/process", json={"prompt": "Should be blocked"})
        assert ai_response.status_code == 403

        # Step 3: Attempt increment - should be blocked
        increment_response = client.post("/api/ai/usage/increment")
        assert increment_response.status_code == 403

    def test_concurrent_users_isolation(self, client: TestClient, session: Session):
        """Test that usage limits are properly isolated between users."""
        from tests.utils.test_data_factory import TestDataFactory

        # Create two test users using factory
        user1 = TestDataFactory.create_user(
            id=1,
            clerk_sub="user1_123",
            email="user1@example.com",
        )
        user2 = TestDataFactory.create_user(
            id=2,
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
            # User1 should be at limit
            app.dependency_overrides[auth_user] = lambda: user1
            response = client.get("/api/ai/usage")
            assert response.status_code == 200
            assert response.json()["can_use_chat"] is False

            # User2 should have full quota
            app.dependency_overrides[auth_user] = lambda: user2
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

    def test_error_recovery_user_journey(self, client: TestClient, session: Session, test_user: User):
        """Test user journey with temporary errors and recovery."""
        current_date = "2023-01-01"

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

    def test_api_consistency_across_endpoints(self, client: TestClient, session: Session, test_user: User):
        """Test that all API endpoints return consistent data formats."""
        current_date = "2023-01-01"

        # Create some usage
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 3)

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

    def test_high_usage_scenario(self, client: TestClient, session: Session, test_user: User):
        """Test scenario with high usage approaching limit."""
        current_date = "2023-01-01"

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
                assert limit_response.status_code == 200
                assert limit_response.json()["can_use_chat"] is False

                # 11th request should fail
                over_limit_response = client.post("/api/ai/process", json={"prompt": "Over limit"})
                assert over_limit_response.status_code == 429

    def test_usage_tracking_accuracy(self, client: TestClient, session: Session, test_user: User):
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
