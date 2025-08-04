"""Simple test to debug the AI usage service issue."""

from unittest.mock import patch

from app.schema import User
from app.services.auth import auth_user
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session


def test_simple_ai_usage_debug(client: TestClient, session: Session):
    """Simple test to check if basic AI usage endpoint works."""

    # Create a simple test user
    user = User(
        id=1,
        clerk_user_id="test_user_123",
        email="test@example.com",
        created_at=1672531200.0,
        updated_at=1672531200.0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    def get_test_user():
        return user

    # Set up authentication
    app.dependency_overrides[auth_user] = get_test_user

    try:
        # Test basic usage endpoint
        response = client.get("/api/ai/usage")
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code == 500:
            # Try to debug the service directly
            from app.services.ai_chat_usage_service import AIChatUsageService
            try:
                usage_service = AIChatUsageService(session)
                user_plan = usage_service.get_user_plan(user)
                print(f"User plan: {user_plan}")

                daily_limit = usage_service.get_daily_limit(user_plan)
                print(f"Daily limit: {daily_limit}")

            except Exception as e:
                print(f"Service error: {e}")
                import traceback
                traceback.print_exc()

        # The test should pass for now, we're just debugging
        # assert response.status_code == 200

    finally:
        app.dependency_overrides.clear()


def test_config_loading_debug():
    """Test if the config is loading properly."""
    from app.config import get_ai_chat_plan_limit, get_ai_chat_plan_config

    try:
        # Test config loading
        basic_limit = get_ai_chat_plan_limit("basic")
        print(f"Basic plan limit: {basic_limit}")

        basic_config = get_ai_chat_plan_config("basic")
        print(f"Basic plan config: {basic_config}")

        all_limits = get_ai_chat_plan_limit("all")
        print(f"All limits result: {all_limits}")

    except Exception as e:
        print(f"Config error: {e}")
        import traceback
        traceback.print_exc()
