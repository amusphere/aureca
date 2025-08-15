"""User factory for creating User objects in tests."""

import time
from uuid import uuid4

from sqlmodel import Session

from app.schema import User


class UserFactory:
    """Factory class for creating User objects using the factory pattern."""

    @staticmethod
    def build(
        id: int | None = None,
        clerk_sub: str | None = None,
        email: str | None = None,
        name: str | None = None,
        created_at: float | None = None,
        **kwargs,
    ) -> User:
        """Build a User object without persisting to database.

        Args:
            id: User ID (auto-generated if None)
            clerk_sub: Clerk subject ID (auto-generated if None)
            email: User email (default test email if None)
            name: User name (default test name if None)
            created_at: Creation timestamp (current time if None)
            **kwargs: Additional keyword arguments for User model

        Returns:
            User object with specified or default values
        """
        defaults = {
            "id": id,
            "clerk_sub": clerk_sub or f"test_user_{uuid4().hex[:8]}",
            "email": email or f"test{uuid4().hex[:8]}@example.com",
            "name": name or "Test User",
            "created_at": created_at or time.time(),
        }
        defaults.update(kwargs)
        return User(**defaults)

    @staticmethod
    def create(
        session: Session,
        id: int | None = None,
        clerk_sub: str | None = None,
        email: str | None = None,
        name: str | None = None,
        created_at: float | None = None,
        **kwargs,
    ) -> User:
        """Create and persist a User object to the database.

        Args:
            session: Database session for persistence
            id: User ID (auto-generated if None)
            clerk_sub: Clerk subject ID (auto-generated if None)
            email: User email (default test email if None)
            name: User name (default test name if None)
            created_at: Creation timestamp (current time if None)
            **kwargs: Additional keyword arguments for User model

        Returns:
            User object persisted to database with refreshed data
        """
        user = UserFactory.build(id=id, clerk_sub=clerk_sub, email=email, name=name, created_at=created_at, **kwargs)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def create_batch(session: Session, count: int, **common_kwargs) -> list[User]:
        """Create multiple User objects in batch.

        Args:
            session: Database session for persistence
            count: Number of users to create
            **common_kwargs: Common attributes to apply to all users

        Returns:
            List of User objects persisted to database
        """
        users = []
        for i in range(count):
            # Create unique values for each user
            unique_kwargs = {
                "clerk_sub": f"batch_user_{i}_{uuid4().hex[:8]}",
                "email": f"batch{i}_{uuid4().hex[:8]}@example.com",
                "name": f"Batch User {i}",
            }
            unique_kwargs.update(common_kwargs)

            user = UserFactory.create(session, **unique_kwargs)
            users.append(user)

        return users
