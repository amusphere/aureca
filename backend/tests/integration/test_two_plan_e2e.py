"""End-to-end tests for 2-plan system (free and standard)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import and_
from sqlmodel import Session, select

from app.database import get_session
from app.schema import User
from app.services.auth import auth_user
from main import app


class TestTwoPlanE2E:
    """Test complete E2E scenarios for 2-plan system."""

    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock dependencies to ensure consistent test behavior."""
        # Mock ClerkService
        with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
            from unittest.mock import MagicMock

            mock_clerk_service = MagicMock()
            mock_get_clerk_service.return_value = mock_clerk_service

            # Default to standard plan for most tests
            mock_clerk_service.get_user_plan.return_value = "standard"

            yield {
                "mock_clerk_service": mock_clerk_service,
            }

    def _setup_user_with_clerk_sub(self, session: Session, test_user: User, clerk_sub: str):
        """Helper to set up user with clerk_sub."""
        test_user.clerk_sub = clerk_sub
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

    def _create_usage_record(self, session: Session, user_id: int, usage_date: str, usage_count: int):
        """Helper to create usage record with specific count."""
        from datetime import datetime

        from app.schema import AIChatUsage

        # Create or update usage record
        existing = session.exec(
            select(AIChatUsage).where(and_(AIChatUsage.user_id == user_id, AIChatUsage.usage_date == usage_date))
        ).first()

        if existing:
            existing.usage_count = usage_count
            existing.updated_at = datetime.now().timestamp()
            session.add(existing)
        else:
            usage_record = AIChatUsage(
                user_id=user_id,
                usage_date=usage_date,
                usage_count=usage_count,
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp(),
            )
            session.add(usage_record)

        session.commit()

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

    def test_free_plan_complete_workflow(
        self, client: TestClient, session: Session, test_user: User, mock_dependencies
    ):
        """Test complete workflow for free plan user."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_free_user")
        self._setup_auth(test_user)

        try:
            # Mock ClerkService to return free plan
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

            # Step 1: Check usage - should show free plan restrictions
            response = client.get("/api/ai/usage")
            assert response.status_code == 200

            data = response.json()
            assert data["plan_name"] == "free"
            assert data["daily_limit"] == 0
            assert data["remaining_count"] == 0
            assert data["current_usage"] == 0
            assert data["can_use_chat"] is False

            # Step 2: Attempt to increment usage - should be blocked
            increment_response = client.post("/api/ai/usage/increment")
            assert increment_response.status_code == 403

            error_data = increment_response.json()
            assert "detail" in error_data
            detail = error_data["detail"]
            assert detail["error_code"] == "PLAN_RESTRICTION"
            assert "現在のプランではAIChatをご利用いただけません" in detail["error"]

            # Step 3: Attempt AI processing - should be blocked
            ai_response = client.post("/api/ai/process", json={"prompt": "Test prompt"})
            assert ai_response.status_code == 403

        finally:
            self._cleanup_auth()

    def test_standard_plan_complete_workflow(
        self, client: TestClient, session: Session, test_user: User, mock_dependencies
    ):
        """Test complete workflow for standard plan user."""
        current_date = "2023-01-01"
        self._setup_user_with_clerk_sub(session, test_user, "clerk_standard_user")
        self._setup_auth(test_user)

        try:
            # Mock ClerkService to return standard plan
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Step 1: Check initial usage - should show full quota
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["plan_name"] == "standard"
                assert data["daily_limit"] == 10
                assert data["remaining_count"] == 10
                assert data["current_usage"] == 0
                assert data["can_use_chat"] is True

                # Step 2: Use AI chat multiple times
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
                    # Use 5 times
                    for i in range(5):
                        ai_response = client.post("/api/ai/process", json={"prompt": f"Test prompt {i + 1}"})
                        assert ai_response.status_code == 200

                # Step 3: Check usage after 5 uses
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 5  # 10 - 5
                assert data["current_usage"] == 5
                assert data["can_use_chat"] is True

                # Step 4: Use remaining quota
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
                    # Use remaining 5 times
                    for i in range(5):
                        ai_response = client.post("/api/ai/process", json={"prompt": f"Final prompt {i + 1}"})
                        assert ai_response.status_code == 200

                # Step 5: Check usage at limit
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 0
                assert data["current_usage"] == 10
                assert data["can_use_chat"] is False

                # Step 6: Attempt to use when at limit - should be blocked
                ai_response = client.post("/api/ai/process", json={"prompt": "Should fail"})
                assert ai_response.status_code == 429

                error_data = ai_response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["error_code"] == "USAGE_LIMIT_EXCEEDED"

        finally:
            self._cleanup_auth()

    def test_plan_upgrade_mid_session(self, client: TestClient, session: Session, test_user: User, mock_dependencies):
        """Test plan upgrade during active session."""
        current_date = "2023-01-01"
        self._setup_user_with_clerk_sub(session, test_user, "clerk_upgrade_user")
        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Start with free plan
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

                # Check initial free plan status
                response = client.get("/api/ai/usage")
                assert response.status_code == 200
                assert response.json()["plan_name"] == "free"
                assert response.json()["can_use_chat"] is False

                # Simulate plan upgrade to standard
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

                # Check upgraded plan status
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["plan_name"] == "standard"
                assert data["daily_limit"] == 10
                assert data["remaining_count"] == 10
                assert data["can_use_chat"] is True

                # Should now be able to use AI chat
                with patch(
                    "app.services.ai.AIHub.process_request",
                    return_value={
                        "success": True,
                        "operator_response": None,
                        "execution_results": [],
                        "summary": {"message": "Upgrade test"},
                        "error": None,
                    },
                ):
                    ai_response = client.post("/api/ai/process", json={"prompt": "Post-upgrade test"})
                    assert ai_response.status_code == 200

                # Verify usage was tracked
                response = client.get("/api/ai/usage")
                assert response.status_code == 200
                assert response.json()["current_usage"] == 1

        finally:
            self._cleanup_auth()

    def test_plan_downgrade_mid_session(self, client: TestClient, session: Session, test_user: User, mock_dependencies):
        """Test plan downgrade during active session."""
        current_date = "2023-01-01"
        self._setup_user_with_clerk_sub(session, test_user, "clerk_downgrade_user")
        self._setup_auth(test_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Start with standard plan and some usage
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"
                self._create_usage_record(session, test_user.id, current_date, 3)

                # Check initial standard plan status
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["plan_name"] == "standard"
                assert data["current_usage"] == 3
                assert data["can_use_chat"] is True

                # Simulate plan downgrade to free
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

                # Check downgraded plan status
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["plan_name"] == "free"
                assert data["daily_limit"] == 0
                assert data["current_usage"] == 3  # Usage history preserved
                assert data["can_use_chat"] is False

                # Should now be blocked from AI chat
                ai_response = client.post("/api/ai/process", json={"prompt": "Should be blocked"})
                assert ai_response.status_code == 403

        finally:
            self._cleanup_auth()

    def test_daily_reset_both_plans(self, client: TestClient, session: Session, test_user: User, mock_dependencies):
        """Test daily reset behavior for both plans."""
        day1_date = "2023-01-01"
        day2_date = "2023-01-02"
        self._setup_user_with_clerk_sub(session, test_user, "clerk_reset_user")
        self._setup_auth(test_user)

        try:
            # Test standard plan reset
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"
            self._create_usage_record(session, test_user.id, day1_date, 10)

            # Day 1 - at limit
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=day1_date,
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 200
                assert response.json()["can_use_chat"] is False

            # Day 2 - should reset
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=day2_date,
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["remaining_count"] == 10  # Full quota restored
                assert data["current_usage"] == 0  # Reset to 0
                assert data["can_use_chat"] is True

            # Test free plan (should remain restricted)
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=day2_date,
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 200

                data = response.json()
                assert data["plan_name"] == "free"
                assert data["can_use_chat"] is False  # Still restricted

        finally:
            self._cleanup_auth()

    def test_concurrent_users_different_plans(self, client: TestClient, session: Session, mock_dependencies):
        """Test concurrent users with different plans."""
        current_date = "2023-01-01"

        # Create two test users
        free_user = User(
            id=1001,
            clerk_user_id="free_user_1001",
            email="free@example.com",
            clerk_sub="clerk_free_concurrent",
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        standard_user = User(
            id=1002,
            clerk_user_id="standard_user_1002",
            email="standard@example.com",
            clerk_sub="clerk_standard_concurrent",
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(free_user)
        session.add(standard_user)
        session.commit()
        session.refresh(free_user)
        session.refresh(standard_user)

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Test free user
                self._setup_auth(free_user)
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

                free_response = client.get("/api/ai/usage")
                assert free_response.status_code == 200
                free_data = free_response.json()
                assert free_data["plan_name"] == "free"
                assert free_data["can_use_chat"] is False

                # Test standard user
                self._setup_auth(standard_user)
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

                standard_response = client.get("/api/ai/usage")
                assert standard_response.status_code == 200
                standard_data = standard_response.json()
                assert standard_data["plan_name"] == "standard"
                assert standard_data["can_use_chat"] is True

                # Verify isolation - free user still restricted
                self._setup_auth(free_user)
                mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

                free_response2 = client.get("/api/ai/usage")
                assert free_response2.status_code == 200
                assert free_response2.json()["can_use_chat"] is False

        finally:
            self._cleanup_auth()

    def test_error_handling_across_plans(
        self, client: TestClient, session: Session, test_user: User, mock_dependencies
    ):
        """Test error handling consistency across both plans."""
        self._setup_user_with_clerk_sub(session, test_user, "clerk_error_user")
        self._setup_auth(test_user)

        try:
            # Test system error with standard plan
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.get_usage_stats",
                side_effect=Exception("Database error"),
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 500

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["error_code"] == "SYSTEM_ERROR"

            # Test system error with free plan
            mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService.get_usage_stats",
                side_effect=Exception("Database error"),
            ):
                response = client.get("/api/ai/usage")
                assert response.status_code == 500

                error_data = response.json()
                assert "detail" in error_data
                detail = error_data["detail"]
                assert detail["error_code"] == "SYSTEM_ERROR"

        finally:
            self._cleanup_auth()
