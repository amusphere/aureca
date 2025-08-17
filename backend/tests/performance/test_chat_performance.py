"""
Performance tests for chat functionality to measure query optimization improvements.
"""

import time
from collections.abc import Generator

import pytest
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import ChatMessage, ChatThread, User
from tests.utils.user_factory import UserFactory


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user for performance tests."""
    return UserFactory.create(session)


@pytest.fixture
def large_chat_thread(session: Session, test_user: User) -> Generator[ChatThread, None, None]:
    """Create a chat thread with many messages for performance testing."""
    # Create thread
    thread = ChatThread(
        user_id=test_user.id, title="Performance Test Thread", created_at=time.time(), updated_at=time.time()
    )
    session.add(thread)
    session.commit()
    session.refresh(thread)

    # Create 1000 messages to test pagination performance
    messages = []
    base_time = time.time() - 86400  # Start 24 hours ago

    for i in range(1000):
        role = "user" if i % 2 == 0 else "assistant"
        message = ChatMessage(
            thread_id=thread.id,
            role=role,
            content=f"Test message {i + 1} with some content to simulate real messages",
            created_at=base_time + (i * 60),  # 1 minute apart
        )
        messages.append(message)
        session.add(message)

    session.commit()

    yield thread

    # Cleanup
    session.delete(thread)
    session.commit()


@pytest.fixture
def multiple_threads(session: Session, test_user: User) -> Generator[list[ChatThread], None, None]:
    """Create multiple threads for user listing performance tests."""
    threads = []
    base_time = time.time() - 86400

    for i in range(100):
        thread = ChatThread(
            user_id=test_user.id,
            title=f"Thread {i + 1}",
            created_at=base_time + (i * 3600),  # 1 hour apart
            updated_at=base_time + (i * 3600) + 1800,  # Updated 30 min later
        )
        session.add(thread)
        threads.append(thread)

    session.commit()

    yield threads

    # Cleanup
    for thread in threads:
        session.delete(thread)
    session.commit()


class TestChatPerformance:
    """Performance tests for chat functionality."""

    @pytest.mark.asyncio
    async def test_message_pagination_performance(self, session: Session, large_chat_thread: ChatThread):
        """Test pagination performance with large message sets."""
        # Test first page
        start_time = time.time()
        messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, large_chat_thread.id, page=1, per_page=30
        )
        first_page_time = time.time() - start_time

        assert len(messages) == 30
        assert total_count == 1000
        assert first_page_time < 0.1  # Should be under 100ms

        # Test middle page
        start_time = time.time()
        messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, large_chat_thread.id, page=15, per_page=30
        )
        middle_page_time = time.time() - start_time

        assert len(messages) == 30
        assert total_count == 1000
        assert middle_page_time < 0.1  # Should be under 100ms

        # Test last page
        start_time = time.time()
        messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, large_chat_thread.id, page=34, per_page=30
        )
        last_page_time = time.time() - start_time

        assert len(messages) == 10  # Last page has remaining messages
        assert total_count == 1000
        assert last_page_time < 0.1  # Should be under 100ms

        print(
            f"Pagination performance: first={first_page_time:.3f}s, "
            f"middle={middle_page_time:.3f}s, last={last_page_time:.3f}s"
        )

    @pytest.mark.asyncio
    async def test_context_retrieval_performance(self, session: Session, large_chat_thread: ChatThread):
        """Test AI context retrieval performance."""
        start_time = time.time()
        messages = await chat_message.get_recent_messages_for_context(session, large_chat_thread.id, limit=30)
        context_time = time.time() - start_time

        assert len(messages) == 30
        assert context_time < 0.05  # Should be under 50ms

        # Verify messages are in chronological order (oldest first)
        for i in range(1, len(messages)):
            assert messages[i].created_at >= messages[i - 1].created_at

        print(f"Context retrieval performance: {context_time:.3f}s")

    @pytest.mark.asyncio
    async def test_thread_listing_performance(self, session: Session, multiple_threads: list[ChatThread]):
        """Test thread listing performance with many threads."""
        user_id = multiple_threads[0].user_id

        # Test unpaginated listing
        start_time = time.time()
        threads = await chat_thread.find_by_user_id(session, user_id)
        listing_time = time.time() - start_time

        assert len(threads) == 100
        assert listing_time < 0.05  # Should be under 50ms

        # Verify threads are ordered by updated_at desc
        for i in range(1, len(threads)):
            assert threads[i].updated_at <= threads[i - 1].updated_at

        # Test paginated listing
        start_time = time.time()
        paginated_threads, total_count = await chat_thread.find_by_user_id_paginated(
            session, user_id, page=1, per_page=20
        )
        paginated_time = time.time() - start_time

        assert len(paginated_threads) == 20
        assert total_count == 100
        assert paginated_time < 0.05  # Should be under 50ms

        print(f"Thread listing performance: full={listing_time:.3f}s, paginated={paginated_time:.3f}s")

    @pytest.mark.asyncio
    async def test_thread_lookup_performance(self, session: Session, multiple_threads: list[ChatThread]):
        """Test thread UUID lookup performance."""
        user_id = multiple_threads[0].user_id
        test_thread = multiple_threads[50]  # Pick a middle thread

        start_time = time.time()
        found_thread = await chat_thread.find_by_uuid(session, test_thread.uuid, user_id)
        lookup_time = time.time() - start_time

        assert found_thread is not None
        assert found_thread.id == test_thread.id
        assert lookup_time < 0.01  # Should be under 10ms

        print(f"Thread UUID lookup performance: {lookup_time:.3f}s")

    @pytest.mark.asyncio
    async def test_message_count_performance(self, session: Session, large_chat_thread: ChatThread):
        """Test message counting performance."""
        start_time = time.time()
        count = await chat_message.count_by_thread_id(session, large_chat_thread.id)
        count_time = time.time() - start_time

        assert count == 1000
        assert count_time < 0.01  # Should be under 10ms

        print(f"Message count performance: {count_time:.3f}s")

    @pytest.mark.asyncio
    async def test_batch_message_creation_performance(self, session: Session, test_user: User):
        """Test batch message creation performance."""
        # Create a thread first
        thread = await chat_thread.create(session, test_user.id, "Batch Test Thread")

        # Prepare batch data
        messages_data = []
        for i in range(100):
            role = "user" if i % 2 == 0 else "assistant"
            messages_data.append({"thread_id": thread.id, "role": role, "content": f"Batch message {i + 1}"})

        # Test batch creation
        start_time = time.time()
        messages = await chat_message.create_batch(session, messages_data)
        batch_time = time.time() - start_time

        assert len(messages) == 100
        assert batch_time < 0.5  # Should be under 500ms

        print(f"Batch message creation performance: {batch_time:.3f}s for 100 messages")

        # Cleanup
        await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)


class TestQueryOptimization:
    """Tests to verify query optimization effectiveness."""

    @pytest.mark.asyncio
    async def test_index_usage_verification(self, session: Session, test_user: User):
        """Verify that queries are using indexes effectively."""
        # This test would ideally use EXPLAIN ANALYZE in PostgreSQL
        # For now, we'll test that queries complete within expected time bounds

        # Create test data
        thread = await chat_thread.create(session, test_user.id, "Index Test")

        # Add some messages
        for i in range(50):
            await chat_message.create(session, thread.id, "user" if i % 2 == 0 else "assistant", f"Message {i}")

        # Test various query patterns that should use indexes
        queries_to_test = [
            # Thread queries
            lambda: chat_thread.find_by_user_id(session, test_user.id),
            lambda: chat_thread.find_by_uuid(session, thread.uuid, test_user.id),
            # Message queries
            lambda: chat_message.find_by_thread_id_paginated(session, thread.id, 1, 10),
            lambda: chat_message.get_recent_messages_for_context(session, thread.id, 10),
            lambda: chat_message.count_by_thread_id(session, thread.id),
        ]

        for i, query_func in enumerate(queries_to_test):
            start_time = time.time()
            await query_func()
            query_time = time.time() - start_time

            # All queries should be very fast with proper indexes
            assert query_time < 0.05, f"Query {i} took {query_time:.3f}s, expected < 0.05s"

        # Cleanup
        await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)
