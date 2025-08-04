"""Test configuration and shared fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.config import config_manager
from app.database import get_session
from app.schema import TaskPriority, Tasks, User
from main import app


# Protect config file from being modified during tests
@pytest.fixture(autouse=True, scope="session")
def protect_config_file():
    """Prevent tests from modifying the actual config file"""
    with patch.object(config_manager, "_save_to_file", return_value=None):
        yield


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
        email="test@example.com",
        created_at=1672531200.0,  # 2023-01-01 00:00:00
        updated_at=1672531200.0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="sample_tasks")
def sample_tasks_fixture(session: Session, test_user: User) -> list[Tasks]:
    """Create sample tasks with different priorities for testing."""
    from app.repositories.tasks import create_task

    tasks = []

    # Create tasks using the repository function to ensure proper handling
    task1 = create_task(
        session=session,
        user_id=test_user.id,
        title="High Priority Task 1",
        description="Urgent task",
        priority=TaskPriority.HIGH,
        expires_at=1672617600.0,  # 2023-01-02 00:00:00
    )
    tasks.append(task1)

    task2 = create_task(
        session=session,
        user_id=test_user.id,
        title="High Priority Task 2",
        description="Another urgent task",
        priority=TaskPriority.HIGH,
        expires_at=1672704000.0,  # 2023-01-03 00:00:00
    )
    tasks.append(task2)

    task3 = create_task(
        session=session,
        user_id=test_user.id,
        title="Middle Priority Task 1",
        description="Moderate importance",
        priority=TaskPriority.MIDDLE,
        expires_at=1672617600.0,  # 2023-01-02 00:00:00
    )
    tasks.append(task3)

    task4 = create_task(
        session=session,
        user_id=test_user.id,
        title="Low Priority Task 1",
        description="Low importance",
        priority=TaskPriority.LOW,
        expires_at=1672531200.0,  # 2023-01-01 00:00:00
    )
    tasks.append(task4)

    task5 = create_task(
        session=session,
        user_id=test_user.id,
        title="No Priority Task 1",
        description="No priority set",
        priority=None,
        expires_at=1672531200.0,  # 2023-01-01 00:00:00
    )
    tasks.append(task5)

    return tasks
