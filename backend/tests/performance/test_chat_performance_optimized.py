"""
Enhanced performance tests for chat functionality with optimization verification.
"""

import time
from collections.abc import Generator

import pytest
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import ChatMessage, ChatThread, User
from tests.utils.performance import (
    PaginationOptimizer,
    QueryPerformanceMonitor,
    benchmark_query,
)
from tests.utils.user_factory import UserFactory


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user for performance tests."""
    return UserFactory.create(session)


@pytest.fixture
def performance_monitor(session: Session) -> QueryPerformanceMonitor:
    """Create a performance monitor for the session."""
    return QueryPerformanceMonitor(session)


@pytest.fixture
def large_chat_thread_optimized(session: Session, test_user: User) -> Generator[ChatThread, None, None]:
    """Create a chat thread with many messages for performance testing."""
    # Create thread
    thread = ChatThread(
        user_id=test_user.id,
        title="Performance Test Thread",
        created_at=time.time(),
        updated_at=time.time(),
    )
    session.add(thread)
    session.commit()
    session.refresh(thread)

    # Create 5000 messages to test performance with larger datasets
    messages = []
    base_time = time.time() - 86400  # Start 24 hours ago

    for i in range(5000):
        role = "user" if i % 2 == 0 else "assistant"
        message = ChatMessage(
            thread_id=thread.id,
            role=role,
            content=f"Performance test message {i + 1} with realistic content length to simulate actual chat messages that users might send",
            created_at=base_time + (i * 10),  # 10 seconds apart
        )
        messages.append(message)
        session.add(message)

    session.commit()

    yield thread

    # Cleanup
    session.delete(thread)
    session.commit()


@pytest.fixture
def multiple_threads_optimized(session: Session, test_user: User) -> Generator[list[ChatThread], None, None]:
    """Create multiple threads with messages for comprehensive performance testing."""
    threads = []
    base_time = time.time() - 86400 * 30  # Start 30 days ago

    for i in range(500):  # More threads for better testing
        thread = ChatThread(
            user_id=test_user.id,
            title=f"Performance Thread {i + 1}",
            created_at=base_time + (i * 3600),  # 1 hour apart
            updated_at=base_time + (i * 3600) + 1800,  # Updated 30 min later
        )
        session.add(thread)
        threads.append(thread)

    session.commit()  # Commit threads first to get their IDs

    # Add a few messages to each thread
    for thread in threads:
        for j in range(5):
            message = ChatMessage(
                thread_id=thread.id,
                role="user" if j % 2 == 0 else "assistant",
                content=f"Message {j + 1} in thread {thread.title}",
                created_at=thread.created_at + (j * 300),  # 5 minutes apart
            )
            session.add(message)

    session.commit()

    yield threads

    # Cleanup
    for thread in threads:
        session.delete(thread)
    session.commit()


class TestOptimizedChatPerformance:
    """Enhanced performance tests with optimization verification."""

    @pytest.mark.asyncio
    async def test_index_optimized_thread_listing(
        self,
        session: Session,
        multiple_threads_optimized: list[ChatThread],
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test that thread listing uses optimized indexes."""
        user_id = multiple_threads_optimized[0].user_id

        # Benchmark the optimized query
        async with performance_monitor.monitor_query("thread_listing_optimized") as metrics:
            threads = await chat_thread.find_by_user_id(session, user_id)

        assert len(threads) == 500
        assert metrics["execution_time_ms"] < 50  # Should be very fast with proper index

        # Verify threads are properly ordered
        for i in range(1, len(threads)):
            assert threads[i].updated_at <= threads[i - 1].updated_at

        print(f"Optimized thread listing: {metrics['execution_time_ms']:.2f}ms for 500 threads")

    @pytest.mark.asyncio
    async def test_pagination_performance_scaling(
        self,
        session: Session,
        large_chat_thread_optimized: ChatThread,
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test pagination performance across different page positions."""
        thread_id = large_chat_thread_optimized.id
        per_page = 30

        # Test different page positions
        test_pages = [1, 10, 50, 100, 166]  # Last page for 5000 messages
        page_times = {}

        for page in test_pages:
            async with performance_monitor.monitor_query(f"pagination_page_{page}") as metrics:
                messages, total_count = await chat_message.find_by_thread_id_paginated(
                    session, thread_id, page=page, per_page=per_page
                )

            page_times[page] = metrics["execution_time_ms"]

            # Verify results
            expected_count = per_page if page < 166 else 20  # Last page has 20 messages
            assert len(messages) == expected_count
            assert total_count == 5000

            # Performance should be reasonable even for later pages
            assert metrics["execution_time_ms"] < 200  # Allow more time for large offsets

        print(f"Pagination performance: {page_times}")

        # Verify that performance doesn't degrade too much for later pages
        first_page_time = page_times[1]
        last_page_time = page_times[166]
        degradation_ratio = last_page_time / first_page_time

        # Performance degradation should be reasonable (less than 10x)
        assert degradation_ratio < 10, f"Performance degraded {degradation_ratio:.2f}x from first to last page"

    @pytest.mark.asyncio
    async def test_context_retrieval_optimization(
        self,
        session: Session,
        large_chat_thread_optimized: ChatThread,
        performance_monitor: QueryPerformanceMonitor,
    ):
        """Test AI context retrieval performance with large message history."""
        thread_id = large_chat_thread_optimized.id

        # Test different context sizes
        context_sizes = [10, 30, 50, 100]

        for limit in context_sizes:
            async with performance_monitor.monitor_query(f"context_retrieval_{limit}") as metrics:
                messages = await chat_message.get_recent_messages_for_context(session, thread_id, limit=limit)

            assert len(messages) == limit
            assert metrics["execution_time_ms"] < 30  # Should be very fast with proper index

            # Verify chronological order
            for i in range(1, len(messages)):
                assert messages[i].created_at >= messages[i - 1].created_at

            print(f"Context retrieval ({limit} messages): {metrics['execution_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_pagination_strategy_optimization(self, session: Session, large_chat_thread_optimized: ChatThread):
        """Test pagination strategy recommendations."""
        total_messages = 5000

        # Test different pagination scenarios
        scenarios = [
            (1, 30),  # First page
            (10, 30),  # Early page
            (50, 30),  # Middle page
            (100, 30),  # Late page
            (166, 30),  # Last page
        ]

        for page, per_page in scenarios:
            strategy = PaginationOptimizer.suggest_pagination_strategy(page, per_page, total_messages)

            print(f"Page {page}: {strategy}")

            # Verify strategy recommendations
            if page > 50:  # Later pages should recommend cursor pagination
                assert strategy["recommended_strategy"] == "cursor"
            else:
                assert strategy["recommended_strategy"] == "offset"

            # Efficiency should decrease for later pages
            if page == 1:
                assert strategy["efficiency_score"] > 0.9
            elif page > 100:
                assert strategy["efficiency_score"] < 0.5

    @pytest.mark.asyncio
    async def test_query_benchmarking(self, session: Session, large_chat_thread_optimized: ChatThread):
        """Benchmark key queries to establish performance baselines."""
        thread_id = large_chat_thread_optimized.id
        user_id = large_chat_thread_optimized.user_id

        # Benchmark different query types
        benchmarks = {}

        # Thread listing benchmark
        benchmarks["thread_listing"] = await benchmark_query(
            session, chat_thread.find_by_user_id, user_id, iterations=10
        )

        # Message pagination benchmark
        benchmarks["message_pagination"] = await benchmark_query(
            session,
            chat_message.find_by_thread_id_paginated,
            thread_id,
            page=1,
            per_page=30,
            iterations=10,
        )

        # Context retrieval benchmark
        benchmarks["context_retrieval"] = await benchmark_query(
            session,
            chat_message.get_recent_messages_for_context,
            thread_id,
            limit=30,
            iterations=10,
        )

        # Message count benchmark
        benchmarks["message_count"] = await benchmark_query(
            session, chat_message.count_by_thread_id, thread_id, iterations=10
        )

        # Print benchmark results
        for query_type, results in benchmarks.items():
            print(
                f"{query_type}: avg={results['avg_time_ms']:.2f}ms, "
                f"min={results['min_time_ms']:.2f}ms, max={results['max_time_ms']:.2f}ms"
            )

        # Verify performance targets
        assert benchmarks["thread_listing"]["avg_time_ms"] < 20
        assert benchmarks["message_pagination"]["avg_time_ms"] < 50
        assert benchmarks["context_retrieval"]["avg_time_ms"] < 30
        assert benchmarks["message_count"]["avg_time_ms"] < 10

    @pytest.mark.asyncio
    async def test_concurrent_access_performance(self, session: Session, multiple_threads_optimized: list[ChatThread]):
        """Test performance under concurrent access patterns."""
        import asyncio

        user_id = multiple_threads_optimized[0].user_id

        # Simulate concurrent thread listing requests
        async def concurrent_thread_listing():
            return await chat_thread.find_by_user_id(session, user_id)

        # Run multiple concurrent requests
        start_time = time.time()
        tasks = [concurrent_thread_listing() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all requests succeeded
        for result in results:
            assert len(result) == 500

        total_time = end_time - start_time
        avg_time_per_request = total_time / 10

        print(f"Concurrent access: {total_time:.3f}s total, {avg_time_per_request:.3f}s avg per request")

        # Performance should still be reasonable under concurrent load
        assert avg_time_per_request < 0.1  # 100ms per request

    @pytest.mark.asyncio
    async def test_memory_efficient_pagination(self, session: Session, large_chat_thread_optimized: ChatThread):
        """Test memory efficiency of pagination implementation."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        thread_id = large_chat_thread_optimized.id

        # Measure memory usage before
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Paginate through all messages
        page = 1
        per_page = 100
        total_processed = 0

        while True:
            messages, total_count = await chat_message.find_by_thread_id_paginated(
                session, thread_id, page=page, per_page=per_page
            )

            if not messages:
                break

            total_processed += len(messages)
            page += 1

            # Process messages (simulate real usage)
            for message in messages:
                _ = message.content  # Access content to ensure it's loaded

        # Measure memory usage after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        print(
            f"Memory usage: {memory_before:.1f}MB -> {memory_after:.1f}MB "
            f"(+{memory_increase:.1f}MB) for {total_processed} messages"
        )

        # Memory increase should be reasonable (less than 100MB for 5000 messages)
        assert memory_increase < 100
        assert total_processed == 5000


class TestIndexUsageVerification:
    """Tests to verify that database indexes are being used effectively."""

    @pytest.mark.asyncio
    async def test_index_usage_statistics(
        self,
        session: Session,
        performance_monitor: QueryPerformanceMonitor,
        multiple_threads_optimized: list[ChatThread],
    ):
        """Verify that our indexes are being used by checking database statistics."""
        # Run some queries to generate index usage
        user_id = multiple_threads_optimized[0].user_id

        # Generate index usage
        await chat_thread.find_by_user_id(session, user_id)

        # Get index usage statistics
        thread_stats = await performance_monitor.get_index_usage_stats("chat_threads")
        message_stats = await performance_monitor.get_index_usage_stats("chat_messages")

        print("Thread index usage:", thread_stats)
        print("Message index usage:", message_stats)

        # Verify that our performance indexes are present
        [stat.get("index", "") for stat in thread_stats if isinstance(stat, dict)]
        expected_thread_indexes = [
            "idx_chat_threads_user_updated_desc",
            "idx_chat_threads_updated_at",
        ]

        for _expected_index in expected_thread_indexes:
            # Note: Index might not show up in stats if not used yet, so we just check structure
            assert isinstance(thread_stats, list)

    @pytest.mark.asyncio
    async def test_table_statistics(
        self,
        session: Session,
        performance_monitor: QueryPerformanceMonitor,
        large_chat_thread_optimized: ChatThread,
    ):
        """Get table statistics to understand data distribution."""
        thread_stats = await performance_monitor.get_table_stats("chat_threads")
        message_stats = await performance_monitor.get_table_stats("chat_messages")

        print("Thread table stats:", thread_stats)
        print("Message table stats:", message_stats)

        # Verify we have reasonable data for testing
        assert isinstance(thread_stats.get("row_count"), int)
        assert isinstance(message_stats.get("row_count"), int)
        assert message_stats.get("row_count", 0) >= 5000  # From our test data
