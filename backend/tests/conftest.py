"""Test configuration and shared fixtures."""

import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Add the backend directory to Python path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Now import app modules after adding to path
from app.database import get_session  # noqa: E402
from app.schema import TaskPriority, Tasks, User  # noqa: E402
from main import app  # noqa: E402


# Test database configuration
@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with the test database session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create a test user."""
    user = User(
        id=1,
        clerk_user_id="test_user_123",
        clerk_sub="test_user_123",  # Add clerk_sub for plan determination
        email="test@example.com",
        created_at=1672531200.0,  # 2023-01-01 00:00:00
        updated_at=1672531200.0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="mock_clerk_service")
def mock_clerk_service_fixture() -> Generator[MagicMock, None, None]:
    """Create a mock ClerkService with standard responses."""
    with patch("app.services.clerk_service.get_clerk_service") as mock_get_service:
        mock_service = MagicMock()

        # Set up standard responses
        mock_service.get_user_plan.return_value = "standard"
        mock_service.get_subscription_info.return_value = {
            "plan": "standard",
            "status": "active",
            "renews_at": "2024-12-31T23:59:59Z",
        }
        mock_service.has_subscription.return_value = True
        mock_service.has_active_subscription.return_value = True

        mock_get_service.return_value = mock_service
        yield mock_service


@pytest.fixture(name="mock_ai_usage_repository")
def mock_ai_usage_repository_fixture() -> Generator[MagicMock, None, None]:
    """Create a mock AIChatUsageRepository with standard method behaviors."""
    with patch("app.repositories.ai_chat_usage.AIChatUsageRepository") as mock_repo_class:
        mock_repo = MagicMock()

        # Set up standard responses for static methods
        mock_repo.get_current_usage_count.return_value = 0
        mock_repo.increment_usage_count.return_value = 1
        mock_repo.get_daily_usage_record.return_value = None
        mock_repo.reset_daily_usage.return_value = None
        mock_repo.bulk_reset_daily_usage.return_value = 0
        mock_repo.get_usage_stats.return_value = {"usage_count": 0, "updated_at": None, "usage_date": "2023-01-01"}
        mock_repo.cleanup_old_records.return_value = 0
        mock_repo.get_usage_history.return_value = []
        mock_repo.create_daily_usage.return_value = None

        # Make the class return the mock instance
        mock_repo_class.return_value = mock_repo

        # Also mock the static methods directly on the class
        mock_repo_class.get_current_usage_count = mock_repo.get_current_usage_count
        mock_repo_class.increment_usage_count = mock_repo.increment_usage_count
        mock_repo_class.get_daily_usage_record = mock_repo.get_daily_usage_record
        mock_repo_class.reset_daily_usage = mock_repo.reset_daily_usage
        mock_repo_class.bulk_reset_daily_usage = mock_repo.bulk_reset_daily_usage
        mock_repo_class.get_usage_stats = mock_repo.get_usage_stats
        mock_repo_class.cleanup_old_records = mock_repo.cleanup_old_records
        mock_repo_class.get_usage_history = mock_repo.get_usage_history
        mock_repo_class.create_daily_usage = mock_repo.create_daily_usage

        yield mock_repo


@pytest.fixture(name="setup_app_overrides")
def setup_app_overrides_fixture(
    mock_clerk_service: MagicMock,
    mock_ai_usage_repository: MagicMock,
) -> Generator[None, None, None]:
    """Setup FastAPI dependency overrides for integration tests.

    This fixture configures all necessary dependency overrides for integration tests,
    ensuring proper test isolation and cleanup.
    """
    from app.services.clerk_service import get_clerk_service

    # Store existing overrides to preserve them
    existing_overrides = app.dependency_overrides.copy()

    # Set up dependency overrides
    app.dependency_overrides[get_clerk_service] = lambda: mock_clerk_service

    # For repository, we need to override the class itself since it's used directly
    # This is handled by the mock_ai_usage_repository fixture

    yield

    # Clean up: restore original overrides
    app.dependency_overrides.clear()
    app.dependency_overrides.update(existing_overrides)


@pytest.fixture(name="sample_tasks")
def sample_tasks_fixture(session: Session, test_user: User) -> list[Tasks]:
    """Create sample tasks with different priorities for testing using factory pattern."""
    from tests.utils.test_data_factory import TestDataFactory

    tasks = []

    # Create tasks using the factory pattern for standardized test data generation
    task1 = TestDataFactory.create_task(
        user_id=test_user.id,
        title="High Priority Task 1",
        description="Urgent task",
        priority=TaskPriority.HIGH,
        expires_at=1672617600.0,  # 2023-01-02 00:00:00
    )
    session.add(task1)
    tasks.append(task1)

    task2 = TestDataFactory.create_task(
        user_id=test_user.id,
        title="High Priority Task 2",
        description="Another urgent task",
        priority=TaskPriority.HIGH,
        expires_at=1672704000.0,  # 2023-01-03 00:00:00
    )
    session.add(task2)
    tasks.append(task2)

    task3 = TestDataFactory.create_task(
        user_id=test_user.id,
        title="Middle Priority Task 1",
        description="Moderate importance",
        priority=TaskPriority.MIDDLE,
        expires_at=1672617600.0,  # 2023-01-02 00:00:00
    )
    session.add(task3)
    tasks.append(task3)

    task4 = TestDataFactory.create_task(
        user_id=test_user.id,
        title="Low Priority Task 1",
        description="Low importance",
        priority=TaskPriority.LOW,
        expires_at=1672531200.0,  # 2023-01-01 00:00:00
    )
    session.add(task4)
    tasks.append(task4)

    task5 = TestDataFactory.create_task(
        user_id=test_user.id,
        title="No Priority Task 1",
        description="No priority set",
        priority=None,
        expires_at=1672531200.0,  # 2023-01-01 00:00:00
    )
    session.add(task5)
    tasks.append(task5)

    session.commit()

    # Refresh all tasks to get their IDs
    for task in tasks:
        session.refresh(task)

    return tasks
