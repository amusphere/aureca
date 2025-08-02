"""Unit tests for AI chat usage repository functionality."""

from app.repositories.ai_chat_usage import (
    create_daily_usage,
    get_current_usage_count,
    get_daily_usage,
    get_usage_history,
    increment_daily_usage,
    update_usage_count,
)
from app.schema import User
from sqlmodel import Session


class TestAIChatUsageRepository:
    """Unit tests for AI chat usage repository functionality."""

    def test_create_daily_usage(self, session: Session, test_user: User):
        """Test creating a new daily usage record."""
        usage_date = "2023-01-02"
        usage_count = 5

        usage_log = create_daily_usage(
            session=session,
            user_id=test_user.id,
            usage_date=usage_date,
            usage_count=usage_count,
        )

        assert usage_log.user_id == test_user.id
        assert usage_log.usage_date == usage_date
        assert usage_log.usage_count == usage_count
        assert usage_log.id is not None
        assert usage_log.created_at > 0
        assert usage_log.updated_at > 0

    def test_create_daily_usage_default_count(self, session: Session, test_user: User):
        """Test creating a daily usage record with default count."""
        usage_date = "2023-01-02"

        usage_log = create_daily_usage(
            session=session, user_id=test_user.id, usage_date=usage_date
        )

        assert usage_log.usage_count == 1  # Default value

    def test_get_daily_usage_existing(self, session: Session, test_user: User):
        """Test getting an existing daily usage record."""
        usage_date = "2023-01-02"

        # Create a usage record
        created_log = create_daily_usage(
            session=session, user_id=test_user.id, usage_date=usage_date, usage_count=3
        )

        # Retrieve it
        retrieved_log = get_daily_usage(session, test_user.id, usage_date)

        assert retrieved_log is not None
        assert retrieved_log.id == created_log.id
        assert retrieved_log.user_id == test_user.id
        assert retrieved_log.usage_date == usage_date
        assert retrieved_log.usage_count == 3

    def test_get_daily_usage_nonexistent(self, session: Session, test_user: User):
        """Test getting a non-existent daily usage record."""
        usage_date = "2023-01-02"

        retrieved_log = get_daily_usage(session, test_user.id, usage_date)

        assert retrieved_log is None

    def test_get_current_usage_count_existing(self, session: Session, test_user: User):
        """Test getting current usage count for existing record."""
        usage_date = "2023-01-02"
        expected_count = 7

        create_daily_usage(
            session=session,
            user_id=test_user.id,
            usage_date=usage_date,
            usage_count=expected_count,
        )

        count = get_current_usage_count(session, test_user.id, usage_date)

        assert count == expected_count

    def test_get_current_usage_count_nonexistent(
        self, session: Session, test_user: User
    ):
        """Test getting current usage count for non-existent record."""
        usage_date = "2023-01-02"

        count = get_current_usage_count(session, test_user.id, usage_date)

        assert count == 0

    def test_increment_daily_usage_new_record(self, session: Session, test_user: User):
        """Test incrementing usage for a new record (creates with count 1)."""
        usage_date = "2023-01-02"

        usage_log = increment_daily_usage(session, test_user.id, usage_date)

        assert usage_log.user_id == test_user.id
        assert usage_log.usage_date == usage_date
        assert usage_log.usage_count == 1

    def test_increment_daily_usage_existing_record(
        self, session: Session, test_user: User
    ):
        """Test incrementing usage for an existing record."""
        usage_date = "2023-01-02"
        initial_count = 5

        # Create initial record
        create_daily_usage(
            session=session,
            user_id=test_user.id,
            usage_date=usage_date,
            usage_count=initial_count,
        )

        # Increment it
        updated_log = increment_daily_usage(session, test_user.id, usage_date)

        assert updated_log.usage_count == initial_count + 1
        assert updated_log.user_id == test_user.id
        assert updated_log.usage_date == usage_date

    def test_increment_daily_usage_multiple_times(
        self, session: Session, test_user: User
    ):
        """Test incrementing usage multiple times."""
        usage_date = "2023-01-02"

        # First increment (creates record)
        log1 = increment_daily_usage(session, test_user.id, usage_date)
        assert log1.usage_count == 1

        # Second increment
        log2 = increment_daily_usage(session, test_user.id, usage_date)
        assert log2.usage_count == 2
        assert log2.id == log1.id  # Same record

        # Third increment
        log3 = increment_daily_usage(session, test_user.id, usage_date)
        assert log3.usage_count == 3
        assert log3.id == log1.id  # Same record

    def test_update_usage_count_existing(self, session: Session, test_user: User):
        """Test updating usage count for existing record."""
        usage_date = "2023-01-02"
        initial_count = 3
        new_count = 10

        # Create initial record
        create_daily_usage(
            session=session,
            user_id=test_user.id,
            usage_date=usage_date,
            usage_count=initial_count,
        )

        # Update count
        updated_log = update_usage_count(session, test_user.id, usage_date, new_count)

        assert updated_log.usage_count == new_count
        assert updated_log.user_id == test_user.id
        assert updated_log.usage_date == usage_date

    def test_update_usage_count_nonexistent(self, session: Session, test_user: User):
        """Test updating usage count for non-existent record (creates new)."""
        usage_date = "2023-01-02"
        new_count = 15

        updated_log = update_usage_count(session, test_user.id, usage_date, new_count)

        assert updated_log.usage_count == new_count
        assert updated_log.user_id == test_user.id
        assert updated_log.usage_date == usage_date

    def test_get_usage_history(self, session: Session, test_user: User):
        """Test getting usage history for a user."""
        # Create multiple usage records
        dates_and_counts = [
            ("2023-01-01", 5),
            ("2023-01-02", 3),
            ("2023-01-03", 8),
            ("2023-01-04", 2),
        ]

        for date, count in dates_and_counts:
            create_daily_usage(session, test_user.id, date, count)

        # Get history
        history = get_usage_history(session, test_user.id)

        assert len(history) == 4

        # Should be ordered by date descending
        expected_dates = ["2023-01-04", "2023-01-03", "2023-01-02", "2023-01-01"]
        actual_dates = [log.usage_date for log in history]
        assert actual_dates == expected_dates

    def test_get_usage_history_with_limit(self, session: Session, test_user: User):
        """Test getting usage history with limit."""
        # Create 5 usage records
        for i in range(1, 6):
            date = f"2023-01-0{i}"
            create_daily_usage(session, test_user.id, date, i)

        # Get history with limit of 3
        history = get_usage_history(session, test_user.id, limit=3)

        assert len(history) == 3

        # Should get the 3 most recent dates
        expected_dates = ["2023-01-05", "2023-01-04", "2023-01-03"]
        actual_dates = [log.usage_date for log in history]
        assert actual_dates == expected_dates

    def test_get_usage_history_empty(self, session: Session, test_user: User):
        """Test getting usage history when no records exist."""
        history = get_usage_history(session, test_user.id)

        assert len(history) == 0
        assert history == []

    def test_user_isolation(self, session: Session, test_user: User):
        """Test that usage records are properly isolated by user."""
        # Create another user
        other_user = User(clerk_sub="other_user_123", email="other@example.com")
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        usage_date = "2023-01-02"

        # Create usage records for both users
        create_daily_usage(session, test_user.id, usage_date, 5)
        create_daily_usage(session, other_user.id, usage_date, 10)

        # Verify isolation
        user1_usage = get_daily_usage(session, test_user.id, usage_date)
        user2_usage = get_daily_usage(session, other_user.id, usage_date)

        assert user1_usage.usage_count == 5
        assert user2_usage.usage_count == 10
        assert user1_usage.user_id == test_user.id
        assert user2_usage.user_id == other_user.id

    def test_date_isolation(self, session: Session, test_user: User):
        """Test that usage records are properly isolated by date."""
        date1 = "2023-01-01"
        date2 = "2023-01-02"

        # Create usage records for different dates
        create_daily_usage(session, test_user.id, date1, 3)
        create_daily_usage(session, test_user.id, date2, 7)

        # Verify date isolation
        usage1 = get_daily_usage(session, test_user.id, date1)
        usage2 = get_daily_usage(session, test_user.id, date2)

        assert usage1.usage_count == 3
        assert usage2.usage_count == 7
        assert usage1.usage_date == date1
        assert usage2.usage_date == date2

    def test_updated_at_timestamp_on_increment(self, session: Session, test_user: User):
        """Test that updated_at timestamp is properly updated on increment."""
        usage_date = "2023-01-02"

        # Create initial record
        initial_log = create_daily_usage(session, test_user.id, usage_date, 1)
        initial_updated_at = initial_log.updated_at

        # Wait a tiny bit to ensure timestamp difference
        import time

        time.sleep(0.01)

        # Increment usage
        updated_log = increment_daily_usage(session, test_user.id, usage_date)

        assert updated_log.updated_at > initial_updated_at
        assert updated_log.usage_count == 2

    def test_updated_at_timestamp_on_update(self, session: Session, test_user: User):
        """Test that updated_at timestamp is properly updated on count update."""
        usage_date = "2023-01-02"

        # Create initial record
        initial_log = create_daily_usage(session, test_user.id, usage_date, 1)
        initial_updated_at = initial_log.updated_at

        # Wait a tiny bit to ensure timestamp difference
        import time

        time.sleep(0.01)

        # Update count
        updated_log = update_usage_count(session, test_user.id, usage_date, 10)

        assert updated_log.updated_at > initial_updated_at
        assert updated_log.usage_count == 10
