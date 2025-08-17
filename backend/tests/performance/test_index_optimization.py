"""
Performance tests specifically for index optimization verification.
"""

import time

import pytest
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import ChatMessage, ChatThread, User
from tests.utils.performance import QueryPerformanceMonitor, benchmark_query
from tests.utils.user_factory import UserFactory


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user for performance tests."""
    return UserFactory.create(session)


@pytest.fixture
def performance_monitor(session: Session) -> QueryPerformanceMonitor:
    """Create a performance monitor for the session."""
    return QueryPerformanceMonitor(session)


class TestIndexOptimization:
    """Tests to verify database index optimizations are working."""

    @pytest.mark.asyncio
    async def test_thread_listing_with_indexes(
        self,
        session: Session,
        test_user: User,
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test that thread listing uses optimized indexes."""
        # Create test threads
        threads = []
        base_time = time.time() - 86400  # Start 24 hours ago

        for i in range(100):
            thread = ChatThread(
                user_id=test_user.id,
                title=f"Test Thread {i + 1}",
                created_at=base_time + (i * 3600),  # 1 hour apart
                updated_at=base_time + (i * 3600) + 1800,  # Updated 30 min later
            )
            session.add(thread)
            threads.append(thread)

        session.commit()

        try:
            # Benchmark the optimized query
            async with performance_monitor.monitor_query("thread_listing_optimized") as metrics:
                result_threads = await chat_thread.find_by_user_id(session, test_user.id)

            assert len(result_threads) == 100
            assert metrics["execution_time_ms"] < 100  # Should be fast with proper index

            # Verify threads are properly ordered by updated_at DESC
            for i in range(1, len(result_threads)):
                assert result_threads[i].updated_at <= result_threads[i - 1].updated_at

            print(f"Thread listing with indexes: {metrics['execution_time_ms']:.2f}ms for 100 threads")

        finally:
            # Cleanup
            for thread in threads:
                session.delete(thread)
            session.commit()

    @pytest.mark.asyncio
    async def test_message_pagination_with_indexes(
        self,
        session: Session,
        test_user: User,
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test that message pagination uses optimized indexes."""
        # Create a thread with many messages
        thread = ChatThread(
            user_id=test_user.id,
            title="Pagination Test Thread",
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(thread)
        session.commit()
        session.refresh(thread)

        # Create 1000 messages
        messages = []
        base_time = time.time() - 86400

        for i in range(1000):
            role = "user" if i % 2 == 0 else "assistant"
            message = ChatMessage(
                thread_id=thread.id,
                role=role,
                content=f"Test message {i + 1}",
                created_at=base_time + (i * 60),  # 1 minute apart
            )
            messages.append(message)
            session.add(message)

        session.commit()

        try:
            # Test pagination performance
            async with performance_monitor.monitor_query("message_pagination") as metrics:
                paginated_messages, total_count = await chat_message.find_by_thread_id_paginated(
                    session, thread.id, page=1, per_page=30
                )

            assert len(paginated_messages) == 30
            assert total_count == 1000
            assert metrics["execution_time_ms"] < 50  # Should be fast with proper index

            print(f"Message pagination with indexes: {metrics['execution_time_ms']:.2f}ms for 1000 messages")

        finally:
            # Cleanup
            session.delete(thread)
            session.commit()

    @pytest.mark.asyncio
    async def test_context_retrieval_with_indexes(
        self,
        session: Session,
        test_user: User,
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test that AI context retrieval uses optimized indexes."""
        # Create a thread with many messages
        thread = ChatThread(
            user_id=test_user.id,
            title="Context Test Thread",
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(thread)
        session.commit()
        session.refresh(thread)

        # Create 500 messages
        base_time = time.time() - 86400

        for i in range(500):
            role = "user" if i % 2 == 0 else "assistant"
            message = ChatMessage(
                thread_id=thread.id,
                role=role,
                content=f"Context test message {i + 1}",
                created_at=base_time + (i * 120),  # 2 minutes apart
            )
            session.add(message)

        session.commit()

        try:
            # Test context retrieval performance
            async with performance_monitor.monitor_query("context_retrieval") as metrics:
                context_messages = await chat_message.get_recent_messages_for_context(session, thread.id, limit=30)

            assert len(context_messages) == 30
            assert metrics["execution_time_ms"] < 30  # Should be very fast with proper index

            # Verify chronological order (oldest first)
            for i in range(1, len(context_messages)):
                assert context_messages[i].created_at >= context_messages[i - 1].created_at

            print(f"Context retrieval with indexes: {metrics['execution_time_ms']:.2f}ms for 30 recent messages")

        finally:
            # Cleanup
            session.delete(thread)
            session.commit()

    @pytest.mark.asyncio
    async def test_query_benchmarking_with_indexes(self, session: Session, test_user: User):
        """Benchmark key queries to verify index performance improvements."""
        # Create test data
        thread = ChatThread(
            user_id=test_user.id,
            title="Benchmark Test Thread",
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(thread)
        session.commit()
        session.refresh(thread)

        # Create messages
        base_time = time.time() - 86400
        for i in range(200):
            role = "user" if i % 2 == 0 else "assistant"
            message = ChatMessage(
                thread_id=thread.id,
                role=role,
                content=f"Benchmark message {i + 1}",
                created_at=base_time + (i * 60),
            )
            session.add(message)

        session.commit()

        try:
            # Benchmark different query types
            benchmarks = {}

            # Thread listing benchmark
            benchmarks["thread_listing"] = await benchmark_query(
                session, chat_thread.find_by_user_id, test_user.id, iterations=5
            )

            # Message pagination benchmark
            benchmarks["message_pagination"] = await benchmark_query(
                session,
                chat_message.find_by_thread_id_paginated,
                thread.id,
                page=1,
                per_page=30,
                iterations=5,
            )

            # Context retrieval benchmark
            benchmarks["context_retrieval"] = await benchmark_query(
                session,
                chat_message.get_recent_messages_for_context,
                thread.id,
                limit=30,
                iterations=5,
            )

            # Message count benchmark
            benchmarks["message_count"] = await benchmark_query(
                session, chat_message.count_by_thread_id, thread.id, iterations=5
            )

            # Print benchmark results
            for query_type, results in benchmarks.items():
                print(
                    f"{query_type}: avg={results['avg_time_ms']:.2f}ms, "
                    f"min={results['min_time_ms']:.2f}ms, max={results['max_time_ms']:.2f}ms"
                )

            # Verify performance targets with indexes
            assert benchmarks["thread_listing"]["avg_time_ms"] < 50
            assert benchmarks["message_pagination"]["avg_time_ms"] < 50
            assert benchmarks["context_retrieval"]["avg_time_ms"] < 30
            assert benchmarks["message_count"]["avg_time_ms"] < 20

        finally:
            # Cleanup
            session.delete(thread)
            session.commit()

    @pytest.mark.asyncio
    async def test_pagination_efficiency_comparison(self, session: Session, test_user: User):
        """Compare pagination efficiency at different page positions."""
        # Create a thread with many messages
        thread = ChatThread(
            user_id=test_user.id,
            title="Pagination Efficiency Test",
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(thread)
        session.commit()
        session.refresh(thread)

        # Create 2000 messages for meaningful pagination testing
        base_time = time.time() - 86400
        for i in range(2000):
            role = "user" if i % 2 == 0 else "assistant"
            message = ChatMessage(
                thread_id=thread.id,
                role=role,
                content=f"Pagination test message {i + 1}",
                created_at=base_time + (i * 30),  # 30 seconds apart
            )
            session.add(message)

        session.commit()

        try:
            # Test different page positions
            test_pages = [
                1,
                10,
                30,
                50,
                67,
            ]  # Last page for 2000 messages with per_page=30 (2000/30 = 66.67, so page 67)
            page_times = {}

            for page in test_pages:
                start_time = time.time()
                messages, total_count = await chat_message.find_by_thread_id_paginated(
                    session, thread.id, page=page, per_page=30
                )
                end_time = time.time()

                page_times[page] = (end_time - start_time) * 1000  # Convert to ms

                # Verify results
                expected_count = 30 if page < 67 else 20  # Last page has 20 messages (2000 % 30 = 20)
                assert len(messages) == expected_count
                assert total_count == 2000

                print(f"Page {page}: {page_times[page]:.2f}ms")

            # Verify that performance doesn't degrade too much for later pages
            first_page_time = page_times[1]
            last_page_time = page_times[67]
            degradation_ratio = last_page_time / first_page_time if first_page_time > 0 else 1

            print(f"Performance degradation ratio: {degradation_ratio:.2f}x")

            # With proper indexes, degradation should be reasonable (less than 5x)
            assert degradation_ratio < 5, f"Performance degraded {degradation_ratio:.2f}x from first to last page"

        finally:
            # Cleanup
            session.delete(thread)
            session.commit()
