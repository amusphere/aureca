"""Test data factory for creating test objects."""

import time
from datetime import datetime, timedelta
from uuid import uuid4

from app.schema import AIChatUsage, SourceType, TaskPriority, Tasks, TaskSource, User


class TestDataFactory:
    """Factory class for creating test data objects."""

    @staticmethod
    def create_user(
        id: int | None = None,
        clerk_sub: str | None = None,
        email: str | None = None,
        name: str | None = None,
        created_at: float | None = None,
    ) -> User:
        """Create a User object with default or custom values.

        Args:
            id: User ID (auto-generated if None)
            clerk_sub: Clerk subject ID (auto-generated if None)
            email: User email (default test email if None)
            name: User name (default test name if None)
            created_at: Creation timestamp (current time if None)

        Returns:
            User object with specified or default values
        """
        return User(
            id=id,
            clerk_sub=clerk_sub or f"test_user_{uuid4().hex[:8]}",
            email=email or f"test{uuid4().hex[:8]}@example.com",
            name=name or "Test User",
            created_at=created_at or time.time(),
        )

    @staticmethod
    def create_usage_record(
        user_id: int,
        usage_date: str | None = None,
        usage_count: int = 1,
        id: int | None = None,
        created_at: float | None = None,
        updated_at: float | None = None,
    ) -> AIChatUsage:
        """Create an AIChatUsage record with default or custom values.

        Args:
            user_id: ID of the user this usage belongs to
            usage_date: Date in YYYY-MM-DD format (today if None)
            usage_count: Number of usage counts (default 1)
            id: Record ID (auto-generated if None)
            created_at: Creation timestamp (current time if None)
            updated_at: Update timestamp (current time if None)

        Returns:
            AIChatUsage object with specified or default values
        """
        current_time = time.time()
        return AIChatUsage(
            id=id,
            user_id=user_id,
            usage_date=usage_date or datetime.now().strftime("%Y-%m-%d"),
            usage_count=usage_count,
            created_at=created_at or current_time,
            updated_at=updated_at or current_time,
        )

    @staticmethod
    def create_task(
        user_id: int,
        title: str | None = None,
        description: str | None = None,
        completed: bool = False,
        expires_at: float | None = None,
        priority: TaskPriority | None = None,
        id: int | None = None,
        created_at: float | None = None,
        updated_at: float | None = None,
    ) -> Tasks:
        """Create a Tasks object with default or custom values.

        Args:
            user_id: ID of the user this task belongs to
            title: Task title (default test title if None)
            description: Task description (optional)
            completed: Whether task is completed (default False)
            expires_at: Expiration timestamp (1 week from now if None)
            priority: Task priority (optional)
            id: Task ID (auto-generated if None)
            created_at: Creation timestamp (current time if None)
            updated_at: Update timestamp (current time if None)

        Returns:
            Tasks object with specified or default values
        """
        current_time = time.time()
        default_expires_at = (datetime.now() + timedelta(weeks=1)).timestamp()

        return Tasks(
            id=id,
            user_id=user_id,
            title=title or f"Test Task {uuid4().hex[:8]}",
            description=description,
            completed=completed,
            expires_at=expires_at or default_expires_at,
            priority=priority,
            created_at=created_at or current_time,
            updated_at=updated_at or current_time,
        )

    @staticmethod
    def create_task_source(
        task_id: int,
        source_type: SourceType = SourceType.OTHER,
        source_url: str | None = None,
        source_id: str | None = None,
        title: str | None = None,
        content: str | None = None,
        extra_data: str | None = None,
        id: int | None = None,
        created_at: float | None = None,
        updated_at: float | None = None,
    ) -> TaskSource:
        """Create a TaskSource object with default or custom values.

        Args:
            task_id: ID of the task this source belongs to
            source_type: Type of source (default OTHER)
            source_url: URL of the source (optional)
            source_id: External system ID (optional)
            title: Source title (optional)
            content: Source content (optional)
            extra_data: Additional JSON data (optional)
            id: Source ID (auto-generated if None)
            created_at: Creation timestamp (current time if None)
            updated_at: Update timestamp (current time if None)

        Returns:
            TaskSource object with specified or default values
        """
        current_time = time.time()

        return TaskSource(
            id=id,
            task_id=task_id,
            source_type=source_type,
            source_url=source_url,
            source_id=source_id,
            title=title,
            content=content,
            extra_data=extra_data,
            created_at=created_at or current_time,
            updated_at=updated_at or current_time,
        )
