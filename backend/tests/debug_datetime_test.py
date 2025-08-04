"""Test to debug the datetime parsing issue."""
from datetime import UTC


def test_datetime_debug():
    """Test datetime operations that might be causing the issue."""
    from datetime import datetime

    # Simulate _get_reset_time
    now = datetime.now(UTC)
    next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    next_midnight += timedelta(days=1)
    reset_time_iso = next_midnight.isoformat()

    print(f"Reset time ISO: {reset_time_iso}")

    # Test the parsing that might be failing
    try:
        reset_time = datetime.fromisoformat(
            reset_time_iso.replace("Z", "+00:00")
        )
        print(f"Parsed reset time: {reset_time}")

        time_diff = reset_time - now
        hours_until_reset = max(0, int(time_diff.total_seconds() / 3600))
        print(f"Hours until reset: {hours_until_reset}")

    except Exception as e:
        print(f"Datetime parsing error: {e}")
        import traceback
        traceback.print_exc()


def test_usage_service_check_limit_debug():
    """Test the specific method that's failing."""
    import asyncio

    from app.schema import User
    from app.services.ai_chat_usage_service import AIChatUsageService

    # Create test user
    user = User(
        id=1,
        clerk_user_id="test_user_123",
        email="test@example.com",
        created_at=1672531200.0,
        updated_at=1672531200.0,
    )

    # Mock the database session
    class MockSession:
        def exec(self, stmt):
            class MockResult:
                def first(self):
                    return None  # No existing usage
            return MockResult()

    session = MockSession()

    try:
        usage_service = AIChatUsageService(session)

        # Test check_usage_limit directly
        result = asyncio.run(usage_service.check_usage_limit(user))
        print(f"Check limit result: {result}")

    except Exception as e:
        print(f"Service error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_datetime_debug()
    print("---")
    test_usage_service_check_limit_debug()
