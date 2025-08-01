"""Integration tests for task priority sorting functionality."""

from sqlmodel import Session
from app.repositories.tasks import find_tasks, create_task
from app.schema import Tasks, TaskPriority, User


class TestTaskPrioritySorting:
    """Test task priority sorting functionality."""

    def test_priority_sorting_default_enabled(self, session: Session, test_user: User, sample_tasks: list[Tasks]):
        """Test that tasks are sorted by priority by default."""
        tasks = find_tasks(session=session, user_id=test_user.id)

        assert len(tasks) == 5

        # Verify that HIGH priority tasks come first
        high_priority_tasks = [task for task in tasks if task.priority == TaskPriority.HIGH]

        # All HIGH priority tasks should be at the beginning
        assert len(high_priority_tasks) == 2
        assert tasks[0].priority == TaskPriority.HIGH
        assert tasks[1].priority == TaskPriority.HIGH

        # Within HIGH priority, should be sorted by expires_at
        assert tasks[0].expires_at <= tasks[1].expires_at

        # Verify that None priority tasks come last
        none_priority_tasks = [task for task in tasks if task.priority is None]
        assert len(none_priority_tasks) == 1
        assert tasks[-1].priority is None

        # Verify all tasks are present
        task_titles = {task.title for task in tasks}
        expected_titles = {
            "High Priority Task 1",
            "High Priority Task 2",
            "Middle Priority Task 1",
            "Low Priority Task 1",
            "No Priority Task 1"
        }
        assert task_titles == expected_titles

    def test_priority_secondary_sorting_by_expires_at(self, session: Session, test_user: User):
        """Test secondary sorting by expires_at within same priority."""
        from datetime import datetime, timezone

        # Create tasks with same priority but different expires_at
        earlier_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        later_date = datetime(2024, 1, 20, tzinfo=timezone.utc)

        create_task(
            session=session,
            title="Task Later",
            description="Description",
            user_id=test_user.id,
            priority=TaskPriority.HIGH,
            expires_at=later_date
        )

        create_task(
            session=session,
            title="Task Earlier",
            description="Description",
            user_id=test_user.id,
            priority=TaskPriority.HIGH,
            expires_at=earlier_date
        )

        tasks = find_tasks(session=session, user_id=test_user.id)

        # Find HIGH priority tasks and verify ordering
        high_priority_tasks = [task for task in tasks if task.priority == TaskPriority.HIGH]
        assert len(high_priority_tasks) == 2

        # Should be sorted by expires_at within same priority
        task_titles = [task.title for task in high_priority_tasks]
        assert task_titles == ["Task Earlier", "Task Later"]

    def test_priority_sorting_disabled(self, session: Session, test_user: User, sample_tasks: list[Tasks]):
        """Test that priority sorting can be disabled."""
        tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=False)

        # When priority sorting is disabled, tasks should be sorted by expires_at only
        # The earliest expires_at should come first
        earliest_expires_at = min(task.expires_at or float('inf') for task in sample_tasks)

        assert len(tasks) > 0
        assert tasks[0].expires_at == earliest_expires_at

    def test_null_priority_tasks_last(self, session: Session, test_user: User):
        """Test that tasks with null priority appear last."""
        # Create a mix of tasks using create_task
        create_task(
            session=session,
            user_id=test_user.id,
            title="High Task",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )
        create_task(
            session=session,
            user_id=test_user.id,
            title="No Priority Task",
            priority=None,
            expires_at=1672531200.0,  # Earlier date but no priority
        )
        create_task(
            session=session,
            user_id=test_user.id,
            title="Low Task",
            priority=TaskPriority.LOW,
            expires_at=1672704000.0,
        )

        tasks = find_tasks(session=session, user_id=test_user.id)

        # Order should be: High -> Low -> No Priority (despite earlier expires_at)
        expected_titles = ["High Task", "Low Task", "No Priority Task"]
        actual_titles = [task.title for task in tasks]

        assert actual_titles == expected_titles

    def test_completed_tasks_filter(self, session: Session, test_user: User):
        """Test that completed tasks are properly filtered."""
        # Create mix of completed and incomplete tasks using create_task
        create_task(
            session=session,
            user_id=test_user.id,
            title="Incomplete Task",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )

        completed_task = create_task(
            session=session,
            user_id=test_user.id,
            title="Completed Task",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )

        # Manually set completed status after creation
        completed_task.completed = True
        session.add(completed_task)
        session.commit()

        # Test incomplete tasks
        incomplete_tasks = find_tasks(session=session, user_id=test_user.id, completed=False)
        assert len(incomplete_tasks) == 1
        assert incomplete_tasks[0].title == "Incomplete Task"
        assert not incomplete_tasks[0].completed

        # Test completed tasks
        completed_tasks = find_tasks(session=session, user_id=test_user.id, completed=True)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].title == "Completed Task"
        assert completed_tasks[0].completed

    def test_expires_at_filter(self, session: Session, test_user: User):
        """Test that expires_at filter works correctly."""
        current_time = 1672617600.0  # 2023-01-02 00:00:00

        # Create tasks with different expiry times using create_task
        create_task(
            session=session,
            user_id=test_user.id,
            title="Past Task",
            priority=TaskPriority.HIGH,
            expires_at=1672531200.0,  # 2023-01-01 00:00:00 (past)
        )

        create_task(
            session=session,
            user_id=test_user.id,
            title="Future Task",
            priority=TaskPriority.HIGH,
            expires_at=1672704000.0,  # 2023-01-03 00:00:00 (future)
        )

        # Filter by expires_at
        filtered_tasks = find_tasks(
            session=session,
            user_id=test_user.id,
            expires_at=current_time
        )

        # Should only include tasks with expires_at >= current_time
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0].title == "Future Task"
        assert filtered_tasks[0].expires_at >= current_time
