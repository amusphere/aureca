"""Unit tests for ChatThreadRepository."""

import time
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.repositories import chat_thread
from app.schema import User


class TestChatThreadRepository:
    """Unit tests for chat thread repository functionality."""

    @pytest.mark.asyncio
    async def test_create_thread(self, session: Session, test_user: User):
        """Test creating a new chat thread."""
        title = "Test Chat Thread"

        thread = await chat_thread.create(session, test_user.id, title)

        assert thread.id is not None
        assert thread.uuid is not None
        assert thread.user_id == test_user.id
        assert thread.title == title
        assert thread.created_at > 0
        assert thread.updated_at > 0
        assert thread.created_at == thread.updated_at

    @pytest.mark.asyncio
    async def test_create_thread_without_title(self, session: Session, test_user: User):
        """Test creating a thread without a title."""
        thread = await chat_thread.create(session, test_user.id)

        assert thread.id is not None
        assert thread.uuid is not None
        assert thread.user_id == test_user.id
        assert thread.title is None
        assert thread.created_at > 0
        assert thread.updated_at > 0

    @pytest.mark.asyncio
    async def test_find_by_user_id(self, session: Session, test_user: User):
        """Test finding threads by user ID."""
        # Create multiple threads with different timestamps
        thread1 = await chat_thread.create(session, test_user.id, "Thread 1")
        time.sleep(0.01)  # Ensure different timestamps
        thread2 = await chat_thread.create(session, test_user.id, "Thread 2")
        time.sleep(0.01)
        thread3 = await chat_thread.create(session, test_user.id, "Thread 3")

        threads = await chat_thread.find_by_user_id(session, test_user.id)

        assert len(threads) == 3
        # Should be ordered by updated_at desc (most recent first)
        assert threads[0].id == thread3.id
        assert threads[1].id == thread2.id
        assert threads[2].id == thread1.id

    @pytest.mark.asyncio
    async def test_find_by_user_id_empty(self, session: Session, test_user: User):
        """Test finding threads when user has no threads."""
        threads = await chat_thread.find_by_user_id(session, test_user.id)

        assert len(threads) == 0
        assert threads == []

    @pytest.mark.asyncio
    async def test_find_by_uuid(self, session: Session, test_user: User):
        """Test finding a thread by UUID with user permission check."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        found_thread = await chat_thread.find_by_uuid(session, str(thread.uuid), test_user.id)

        assert found_thread is not None
        assert found_thread.id == thread.id
        assert found_thread.uuid == thread.uuid
        assert found_thread.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_find_by_uuid_with_uuid_object(self, session: Session, test_user: User):
        """Test finding a thread by UUID object."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        found_thread = await chat_thread.find_by_uuid(session, thread.uuid, test_user.id)

        assert found_thread is not None
        assert found_thread.id == thread.id

    @pytest.mark.asyncio
    async def test_find_by_uuid_wrong_user(self, session: Session, test_user: User):
        """Test finding a thread by UUID with wrong user ID (should return None)."""
        # Create another user
        other_user = User(
            id=999,
            clerk_sub="other_user_123",
            email="other@example.com",
            name="Other User",
            created_at=time.time(),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        # Try to find with wrong user ID
        found_thread = await chat_thread.find_by_uuid(session, str(thread.uuid), other_user.id)

        assert found_thread is None

    @pytest.mark.asyncio
    async def test_find_by_uuid_nonexistent(self, session: Session, test_user: User):
        """Test finding a thread by non-existent UUID."""
        fake_uuid = str(uuid4())

        found_thread = await chat_thread.find_by_uuid(session, fake_uuid, test_user.id)

        assert found_thread is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, session: Session, test_user: User):
        """Test getting a thread by ID."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        found_thread = await chat_thread.get_by_id(session, thread.id)

        assert found_thread is not None
        assert found_thread.id == thread.id
        assert found_thread.uuid == thread.uuid

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent(self, session: Session):
        """Test getting a thread by non-existent ID."""
        found_thread = await chat_thread.get_by_id(session, 99999)

        assert found_thread is None

    @pytest.mark.asyncio
    async def test_update_title(self, session: Session, test_user: User):
        """Test updating a thread's title."""
        thread = await chat_thread.create(session, test_user.id, "Original Title")
        original_updated_at = thread.updated_at

        time.sleep(0.01)  # Ensure different timestamp
        new_title = "Updated Title"
        updated_thread = await chat_thread.update_title(session, thread.id, new_title)

        assert updated_thread is not None
        assert updated_thread.id == thread.id
        assert updated_thread.title == new_title
        assert updated_thread.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_title_nonexistent(self, session: Session):
        """Test updating title of non-existent thread."""
        updated_thread = await chat_thread.update_title(session, 99999, "New Title")

        assert updated_thread is None

    @pytest.mark.asyncio
    async def test_update_timestamp(self, session: Session, test_user: User):
        """Test updating a thread's timestamp."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")
        original_updated_at = thread.updated_at

        time.sleep(0.01)  # Ensure different timestamp
        updated_thread = await chat_thread.update_timestamp(session, thread.id)

        assert updated_thread is not None
        assert updated_thread.id == thread.id
        assert updated_thread.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_timestamp_nonexistent(self, session: Session):
        """Test updating timestamp of non-existent thread."""
        updated_thread = await chat_thread.update_timestamp(session, 99999)

        assert updated_thread is None

    @pytest.mark.asyncio
    async def test_delete_by_uuid(self, session: Session, test_user: User):
        """Test deleting a thread by UUID with user permission check."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")
        thread_id = thread.id

        result = await chat_thread.delete_by_uuid(session, str(thread.uuid), test_user.id)

        assert result is True

        # Verify thread is deleted
        deleted_thread = await chat_thread.get_by_id(session, thread_id)
        assert deleted_thread is None

    @pytest.mark.asyncio
    async def test_delete_by_uuid_with_uuid_object(self, session: Session, test_user: User):
        """Test deleting a thread by UUID object."""
        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        result = await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_by_uuid_wrong_user(self, session: Session, test_user: User):
        """Test deleting a thread with wrong user ID (should return False)."""
        # Create another user
        other_user = User(
            id=999,
            clerk_sub="other_user_123",
            email="other@example.com",
            name="Other User",
            created_at=time.time(),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        thread = await chat_thread.create(session, test_user.id, "Test Thread")

        # Try to delete with wrong user ID
        result = await chat_thread.delete_by_uuid(session, str(thread.uuid), other_user.id)

        assert result is False

        # Verify thread still exists
        existing_thread = await chat_thread.get_by_id(session, thread.id)
        assert existing_thread is not None

    @pytest.mark.asyncio
    async def test_delete_by_uuid_nonexistent(self, session: Session, test_user: User):
        """Test deleting a non-existent thread."""
        fake_uuid = str(uuid4())

        result = await chat_thread.delete_by_uuid(session, fake_uuid, test_user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_count_by_user_id(self, session: Session, test_user: User):
        """Test counting threads for a user."""
        # Initially no threads
        count = await chat_thread.count_by_user_id(session, test_user.id)
        assert count == 0

        # Create some threads
        await chat_thread.create(session, test_user.id, "Thread 1")
        await chat_thread.create(session, test_user.id, "Thread 2")
        await chat_thread.create(session, test_user.id, "Thread 3")

        count = await chat_thread.count_by_user_id(session, test_user.id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_find_by_user_id_paginated(self, session: Session, test_user: User):
        """Test finding threads with pagination."""
        # Create 5 threads
        threads = []
        for i in range(5):
            thread = await chat_thread.create(session, test_user.id, f"Thread {i + 1}")
            threads.append(thread)
            time.sleep(0.01)  # Ensure different timestamps

        # Test first page (3 items per page)
        page1_threads, total_count = await chat_thread.find_by_user_id_paginated(
            session, test_user.id, page=1, per_page=3
        )

        assert len(page1_threads) == 3
        assert total_count == 5
        # Should be ordered by updated_at desc (most recent first)
        assert page1_threads[0].title == "Thread 5"
        assert page1_threads[1].title == "Thread 4"
        assert page1_threads[2].title == "Thread 3"

        # Test second page
        page2_threads, total_count = await chat_thread.find_by_user_id_paginated(
            session, test_user.id, page=2, per_page=3
        )

        assert len(page2_threads) == 2
        assert total_count == 5
        assert page2_threads[0].title == "Thread 2"
        assert page2_threads[1].title == "Thread 1"

    @pytest.mark.asyncio
    async def test_find_by_user_id_paginated_empty(self, session: Session, test_user: User):
        """Test pagination with no threads."""
        threads, total_count = await chat_thread.find_by_user_id_paginated(session, test_user.id, page=1, per_page=10)

        assert len(threads) == 0
        assert total_count == 0

    @pytest.mark.asyncio
    async def test_user_isolation(self, session: Session, test_user: User):
        """Test that threads are properly isolated by user."""
        # Create another user
        other_user = User(
            id=999,
            clerk_sub="other_user_123",
            email="other@example.com",
            name="Other User",
            created_at=time.time(),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        # Create threads for both users
        user1_thread = await chat_thread.create(session, test_user.id, "User 1 Thread")
        user2_thread = await chat_thread.create(session, other_user.id, "User 2 Thread")

        # Verify user isolation
        user1_threads = await chat_thread.find_by_user_id(session, test_user.id)
        user2_threads = await chat_thread.find_by_user_id(session, other_user.id)

        assert len(user1_threads) == 1
        assert len(user2_threads) == 1
        assert user1_threads[0].id == user1_thread.id
        assert user2_threads[0].id == user2_thread.id

        # Verify count isolation
        user1_count = await chat_thread.count_by_user_id(session, test_user.id)
        user2_count = await chat_thread.count_by_user_id(session, other_user.id)

        assert user1_count == 1
        assert user2_count == 1
