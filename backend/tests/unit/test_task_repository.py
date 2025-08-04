"""Unit tests for task repository priority functionality."""

from app.repositories.tasks import create_task, find_tasks, update_task
from app.schema import TaskPriority, User
from sqlmodel import Session


class TestTaskRepositoryPriority:
    """Unit tests for task repository priority functionality."""

    def test_create_task_with_priority(self, session: Session, test_user: User):
        """Test creating a task with priority."""
        task = create_task(
            session=session,
            user_id=test_user.id,
            title="High Priority Task",
            description="This is urgent",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )

        assert task.priority == TaskPriority.HIGH
        assert task.title == "High Priority Task"
        assert task.description == "This is urgent"
        assert task.user_id == test_user.id
        assert not task.completed

    def test_create_task_without_priority(self, session: Session, test_user: User):
        """Test creating a task without priority (None)."""
        task = create_task(
            session=session,
            user_id=test_user.id,
            title="No Priority Task",
            description="No priority set",
            priority=None,
        )

        assert task.priority is None
        assert task.title == "No Priority Task"

    def test_update_task_priority(self, session: Session, test_user: User):
        """Test updating a task's priority."""
        # Create initial task
        task = create_task(
            session=session,
            user_id=test_user.id,
            title="Task to Update",
            priority=TaskPriority.LOW,
        )

        original_id = task.id

        # Update priority
        updated_task = update_task(
            session=session, id=task.id, priority=TaskPriority.HIGH
        )

        assert updated_task is not None
        assert updated_task.id == original_id
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.title == "Task to Update"  # Other fields unchanged

    def test_update_task_priority_to_none(self, session: Session, test_user: User):
        """Test updating a task's priority to None."""
        # Create initial task with priority
        task = create_task(
            session=session,
            user_id=test_user.id,
            title="Task with Priority",
            priority=TaskPriority.MIDDLE,
        )

        # Update priority to None
        updated_task = update_task(session=session, id=task.id, priority=None)

        assert updated_task is not None
        assert updated_task.priority is None

    def test_find_tasks_priority_sorting_enabled(
        self, session: Session, test_user: User
    ):
        """Test find_tasks with priority sorting enabled."""
        # Create tasks with different priorities
        create_task(
            session,
            test_user.id,
            "Low Task",
            priority=TaskPriority.LOW,
            expires_at=1672617600.0,
        )
        create_task(
            session,
            test_user.id,
            "High Task",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )
        create_task(
            session,
            test_user.id,
            "Middle Task",
            priority=TaskPriority.MIDDLE,
            expires_at=1672617600.0,
        )
        create_task(
            session,
            test_user.id,
            "No Priority Task",
            priority=None,
            expires_at=1672617600.0,
        )

        tasks = find_tasks(
            session=session, user_id=test_user.id, order_by_priority=True
        )

        # Should be ordered: HIGH(1) -> MIDDLE(2) -> LOW(3) -> None(999)
        expected_titles = ["High Task", "Middle Task", "Low Task", "No Priority Task"]
        actual_titles = [task.title for task in tasks]

        assert actual_titles == expected_titles

    def test_find_tasks_priority_sorting_disabled(
        self, session: Session, test_user: User
    ):
        """Test find_tasks with priority sorting disabled."""
        # Create tasks with different priorities and expires_at times
        create_task(
            session,
            test_user.id,
            "Later Task",
            priority=TaskPriority.HIGH,
            expires_at=1672704000.0,
        )
        create_task(
            session,
            test_user.id,
            "Earlier Task",
            priority=TaskPriority.LOW,
            expires_at=1672617600.0,
        )

        tasks = find_tasks(
            session=session, user_id=test_user.id, order_by_priority=False
        )

        # Should be ordered by expires_at when priority sorting is disabled
        assert tasks[0].title == "Earlier Task"
        assert tasks[1].title == "Later Task"

    def test_find_tasks_with_expires_at_filter(self, session: Session, test_user: User):
        """Test find_tasks with expires_at filter."""
        current_time = 1672617600.0  # 2023-01-02 00:00:00

        # Create tasks with different expiry times
        create_task(
            session,
            test_user.id,
            "Past Task",
            priority=TaskPriority.HIGH,
            expires_at=1672531200.0,
        )  # Past
        create_task(
            session,
            test_user.id,
            "Future Task",
            priority=TaskPriority.HIGH,
            expires_at=1672704000.0,
        )  # Future

        # Filter by expires_at
        future_tasks = find_tasks(
            session=session, user_id=test_user.id, expires_at=current_time
        )

        assert len(future_tasks) == 1
        assert future_tasks[0].title == "Future Task"

    def test_find_tasks_completed_filter(self, session: Session, test_user: User):
        """Test find_tasks with completed filter."""
        # Create completed and incomplete tasks
        incomplete_task = create_task(
            session, test_user.id, "Incomplete Task", priority=TaskPriority.HIGH
        )
        incomplete_task.completed = False
        session.add(incomplete_task)

        completed_task = create_task(
            session, test_user.id, "Completed Task", priority=TaskPriority.HIGH
        )
        completed_task.completed = True
        session.add(completed_task)

        session.commit()

        # Test incomplete tasks
        incomplete_tasks = find_tasks(
            session=session, user_id=test_user.id, completed=False
        )
        assert len(incomplete_tasks) == 1
        assert incomplete_tasks[0].title == "Incomplete Task"

        # Test completed tasks
        completed_tasks = find_tasks(
            session=session, user_id=test_user.id, completed=True
        )
        assert len(completed_tasks) == 1
        assert completed_tasks[0].title == "Completed Task"

    def test_find_tasks_user_isolation(self, session: Session, test_user: User):
        """Test that find_tasks properly isolates tasks by user."""
        # Create another user
        other_user = User(
            id=2,
            clerk_user_id="other_user_123",
            email="other@example.com",
            created_at=1672531200.0,
            updated_at=1672531200.0,
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        # Create tasks for both users
        create_task(session, test_user.id, "User 1 Task", priority=TaskPriority.HIGH)
        create_task(session, other_user.id, "User 2 Task", priority=TaskPriority.HIGH)

        # Verify user isolation
        user1_tasks = find_tasks(session=session, user_id=test_user.id)
        user2_tasks = find_tasks(session=session, user_id=other_user.id)

        assert len(user1_tasks) == 1
        assert len(user2_tasks) == 1
        assert user1_tasks[0].title == "User 1 Task"
        assert user2_tasks[0].title == "User 2 Task"

    def test_find_tasks_empty_result(self, session: Session, test_user: User):
        """Test find_tasks with no matching tasks."""
        # No tasks created
        tasks = find_tasks(session=session, user_id=test_user.id)
        assert len(tasks) == 0
        assert tasks == []

    def test_priority_secondary_sorting_by_expires_at(
        self, session: Session, test_user: User
    ):
        """Test that tasks with same priority are sorted by expires_at."""
        # Create multiple high priority tasks with different expiry times
        create_task(
            session,
            test_user.id,
            "High Later",
            priority=TaskPriority.HIGH,
            expires_at=1672704000.0,
        )
        create_task(
            session,
            test_user.id,
            "High Earlier",
            priority=TaskPriority.HIGH,
            expires_at=1672617600.0,
        )
        create_task(
            session,
            test_user.id,
            "High Middle",
            priority=TaskPriority.HIGH,
            expires_at=1672660000.0,
        )

        tasks = find_tasks(
            session=session, user_id=test_user.id, order_by_priority=True
        )

        # All should be high priority, but sorted by expires_at
        high_priority_tasks = [
            task for task in tasks if task.priority == TaskPriority.HIGH
        ]
        assert len(high_priority_tasks) == 3

        # Should be sorted by expires_at (earlier first)
        expected_order = ["High Earlier", "High Middle", "High Later"]
        actual_order = [task.title for task in high_priority_tasks]
        assert actual_order == expected_order
