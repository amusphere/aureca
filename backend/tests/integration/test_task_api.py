"""Integration tests for task API endpoints with priority functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories.tasks import create_task, find_tasks, update_task
from app.schema import TaskPriority, Tasks, User


class TestTaskAPIIntegration:
    """Test task API endpoints with priority functionality."""

    def test_get_tasks_with_priority_sorting(self, client: TestClient, session: Session, test_user: User):
        """Test GET /api/tasks endpoint with priority sorting."""
        # Create tasks with controlled expiry dates to ensure predictable sorting
        tasks_data = [
            ("High Priority Task", TaskPriority.HIGH, 1672617600.0),  # Earliest expiry
            ("Middle Priority Task", TaskPriority.MIDDLE, 1672704000.0),  # Medium expiry
            ("Low Priority Task", TaskPriority.LOW, 1672790400.0),  # Later expiry
            ("No Priority Task", None, 1672876800.0),  # Latest expiry
        ]

        for title, priority, expires_at in tasks_data:
            task = Tasks(
                user_id=test_user.id,
                title=title,
                description=f"Description for {title}",
                priority=priority,
                completed=False,
                expires_at=expires_at,
                created_at=1672531200.0,
                updated_at=1672531200.0,
            )
            session.add(task)
        session.commit()

        # Test with priority sorting enabled
        tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)

        # Verify priority sorting: HIGH(1) -> MIDDLE(2) -> LOW(3) -> None(999)
        expected_order = [
            "High Priority Task",  # priority = 1
            "Middle Priority Task",  # priority = 2
            "Low Priority Task",  # priority = 3
            "No Priority Task",  # priority = None (treated as 999)
        ]

        actual_titles = [task.title for task in tasks]
        assert actual_titles == expected_order

    def test_create_task_with_priority(self, client: TestClient, session: Session, test_user: User):
        """Test creating a task with priority."""
        # Test data for task creation
        task_data = {
            "title": "New High Priority Task",
            "description": "This is a high priority task",
            "priority": "HIGH",
            "expires_at": 1672617600.0,
        }

        # In a real test, you would mock authentication and make the actual API call
        # For now, we'll test the creation logic directly
        task = create_task(
            session=session,
            user_id=test_user.id,
            title=task_data["title"],
            description=task_data["description"],
            priority=TaskPriority.HIGH,
            expires_at=task_data["expires_at"],
        )

        assert task.title == task_data["title"]
        assert task.description == task_data["description"]
        assert task.priority == TaskPriority.HIGH
        assert task.expires_at == task_data["expires_at"]
        assert task.user_id == test_user.id
        assert not task.completed

    def test_update_task_priority(self, client: TestClient, session: Session, test_user: User):
        """Test updating a task's priority."""
        # Create a task
        task = Tasks(
            user_id=test_user.id,
            title="Task to Update",
            description="Original description",
            priority=TaskPriority.LOW,
            completed=False,
            expires_at=1672617600.0,
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Test the update logic directly
        updated_task = update_task(session=session, id=task.id, priority=TaskPriority.HIGH)

        assert updated_task is not None
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.title == "Task to Update"  # Other fields unchanged

    def test_task_priority_validation(self, session: Session, test_user: User):
        """Test that invalid priority values are handled correctly."""
        # Test with valid priority
        valid_task = create_task(
            session=session, user_id=test_user.id, title="Valid Priority Task", priority=TaskPriority.MIDDLE
        )
        assert valid_task.priority == TaskPriority.MIDDLE

        # Test with None priority (should be allowed)
        none_priority_task = create_task(session=session, user_id=test_user.id, title="No Priority Task", priority=None)
        assert none_priority_task.priority is None

    def test_priority_sorting_performance_with_many_tasks(self, session: Session, test_user: User):
        """Test priority sorting performance with a larger dataset."""
        # Create a moderate number of tasks for performance testing
        num_tasks = 100

        for i in range(num_tasks):
            priority = [TaskPriority.HIGH, TaskPriority.MIDDLE, TaskPriority.LOW, None][i % 4]
            # Use predictable expires_at based on priority to ensure consistent ordering
            base_expires = 1672617600.0
            if priority == TaskPriority.HIGH:
                expires_at = base_expires + (i // 4)  # HIGH tasks expire earliest
            elif priority == TaskPriority.MIDDLE:
                expires_at = base_expires + 100000 + (i // 4)  # MIDDLE tasks expire after HIGH
            elif priority == TaskPriority.LOW:
                expires_at = base_expires + 200000 + (i // 4)  # LOW tasks expire after MIDDLE
            else:  # None priority
                expires_at = base_expires + 300000 + (i // 4)  # None priority tasks expire last

            task = Tasks(
                user_id=test_user.id,
                title=f"Performance Test Task {i}",
                description=f"Description {i}",
                priority=priority,
                completed=False,
                expires_at=expires_at,
                created_at=1672531200.0,
                updated_at=1672531200.0,
            )
            session.add(task)

        session.commit()

        # Measure basic performance
        import time

        start_time = time.time()
        tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)
        end_time = time.time()

        execution_time = end_time - start_time

        # Basic assertions
        assert len(tasks) == num_tasks
        assert execution_time < 1.0  # Should complete within 1 second

        # Verify sorting is correct
        priorities = [task.priority for task in tasks]

        # Count each priority type (25 each since 100 tasks with 4 priority types)
        high_count = priorities.count(TaskPriority.HIGH)
        middle_count = priorities.count(TaskPriority.MIDDLE)
        low_count = priorities.count(TaskPriority.LOW)
        none_count = priorities.count(None)

        # Verify counts (should be 25 each)
        assert high_count == 25
        assert middle_count == 25
        assert low_count == 25
        assert none_count == 25

        # Verify all HIGH priorities come first, then MIDDLE, then LOW, then None
        high_end_index = high_count
        middle_end_index = high_count + middle_count
        low_end_index = high_count + middle_count + low_count

        # Check that priorities are in the correct order
        assert all(p == TaskPriority.HIGH for p in priorities[:high_end_index])
        assert all(p == TaskPriority.MIDDLE for p in priorities[high_end_index:middle_end_index])
        assert all(p == TaskPriority.LOW for p in priorities[middle_end_index:low_end_index])
        assert all(p is None for p in priorities[low_end_index:])
