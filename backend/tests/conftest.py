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

    # Store existing overrides to preserve them
    existing_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    # Restore original overrides instead of clearing all
    app.dependency_overrides.clear()
    app.dependency_overrides.update(existing_overrides)


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
    """Create a real AIChatUsageRepository for integration tests.

    For integration tests, we want to use the real repository with the test database
    rather than mocking it completely.
    """
    from app.repositories.ai_chat_usage import AIChatUsageRepository

    # Return the real repository class for integration tests
    yield AIChatUsageRepository()


@pytest.fixture(name="ai_chat_usage_service")
def ai_chat_usage_service_fixture(
    session: Session,
    mock_clerk_service: MagicMock,
    mock_ai_usage_repository: MagicMock,
):
    """Create AIChatUsageService with mocked dependencies."""
    from app.services.ai_chat_usage_service import AIChatUsageService

    return AIChatUsageService(
        session=session,
        clerk_service=mock_clerk_service,
        usage_repository=mock_ai_usage_repository,
    )


@pytest.fixture(name="setup_app_overrides")
def setup_app_overrides_fixture(
    mock_clerk_service: MagicMock,
    mock_ai_usage_repository: MagicMock,
    ai_chat_usage_service,
) -> Generator[None, None, None]:
    """Setup FastAPI dependency overrides for integration tests.

    This fixture configures all necessary dependency overrides for integration tests,
    ensuring proper test isolation and cleanup.
    """
    from app.services.ai_chat_usage_service import AIChatUsageService
    from app.services.clerk_service import get_clerk_service

    # Store existing overrides to preserve them
    existing_overrides = app.dependency_overrides.copy()

    # Set up dependency overrides
    app.dependency_overrides[get_clerk_service] = lambda: mock_clerk_service

    # Override the service creation by patching the constructor
    def get_ai_chat_usage_service(session: Session):
        return AIChatUsageService(
            session=session,
            clerk_service=mock_clerk_service,
            usage_repository=mock_ai_usage_repository,
        )

    # Patch the service instantiation in the router
    with patch("app.routers.api.ai_assistant.AIChatUsageService", side_effect=get_ai_chat_usage_service):
        yield

    # Clean up: restore original overrides but preserve session override
    session_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides.clear()
    app.dependency_overrides.update(existing_overrides)
    if session_override:
        app.dependency_overrides[get_session] = session_override


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
