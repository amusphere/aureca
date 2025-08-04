"""Test to debug the concurrent users isolation issue."""

from unittest.mock import patch

from app.repositories import ai_chat_usage
from app.schema import User
from app.services.auth import auth_user
from app.services.ai_chat_usage_service import AIChatUsageService
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session
import asyncio


async def test_debug_concurrent_users_isolation(client: TestClient, session: Session):
    """Debug the concurrent users isolation issue."""

    def _setup_auth(test_user: User):
        """Helper to setup authentication override."""
        def get_test_user():
            return test_user
        app.dependency_overrides[auth_user] = get_test_user

    def _cleanup_auth():
        """Helper to cleanup authentication override."""
        app.dependency_overrides.clear()

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
            _setup_auth(user1)
            response = client.get("/api/ai/usage")
            assert response.status_code == 429
            _cleanup_auth()

            # User2 should have full quota - test this manually
            _setup_auth(user2)

            # Debug: Manually test the service
            try:
                usage_service = AIChatUsageService(session)
                print(f"User2 ID: {user2.id}")
                print(f"Current date: {current_date}")

                # Check user plan
                user_plan = usage_service.get_user_plan(user2)
                print(f"User plan: {user_plan}")

                # Check daily limit
                daily_limit = usage_service.get_daily_limit(user_plan)
                print(f"Daily limit: {daily_limit}")

                # Check current usage
                current_usage = ai_chat_usage.get_current_usage_count(
                    session, user2.id, current_date
                )
                print(f"Current usage: {current_usage}")

                # Get full stats
                stats = await usage_service.get_usage_stats(user2)
                print(f"Stats: {stats}")

            except Exception as e:
                print(f"Exception in service: {e}")
                import traceback
                traceback.print_exc()

            response = client.get("/api/ai/usage")
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")

    finally:
        _cleanup_auth()
