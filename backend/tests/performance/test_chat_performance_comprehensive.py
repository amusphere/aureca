"""
Comprehensive performance tests for AI chat history feature.
Tests performance under various load conditions and data sizes.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from main import app
from tests.utils.performance import QueryPerformanceMonitor, benchmark_query


class TestChatPerformanceComprehensive:
    """Comprehensive performance tests for chat functionality."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, test_user: User):
        """Setup authentication for all tests."""
        from app.services.auth import auth_user

        app.dependency_overrides[auth_user] = lambda: test_user
        yield
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    @pytest.fixture
    async def performance_test_data(self, session: Session, test_user: User):
        """Create comprehensive test data for performance testing."""
        threads = []

        # Create 10 threads with varying message counts
        for i in range(10):
            thread = await chat_thread.create(session, test_user.id, f"Performance Thread {i + 1}")
            threads.append(thread)

            # Create different numbers of messages per thread
            message_count = (i + 1) * 50  # 50, 100, 150, ..., 500 messages

            for j in range(message_count):
                role = "user" if j % 2 == 0 else "assistant"
                content = f"Performance test message {j + 1} in thread {i + 1} with some additional content to simulate real messages"
                await chat_message.create(session, thread.id, role, content)

        yield threads

        # Cleanup
        for thread in threads:
            await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)

    @pytest.mark.asyncio
    async def test_thread_listing_performance_with_scale(
        self, session: Session, performance_test_data, test_user: User
    ):
        """Test thread listing performance with various data scales."""
        monitor = QueryPerformanceMonitor(session)

        # Test unpaginated listing
        async with monitor.monitor_query("thread_listing_full") as metrics:
            threads = await chat_thread.find_by_user_id(session, test_user.id)

        assert len(threads) == 10
        assert metrics["execution_time"] < 0.1  # Should be under 100ms
        print(f"Full thread listing: {metrics['execution_time_ms']:.2f}ms")

        # Test paginated listing with different page sizes
        page_sizes = [5, 10, 20]
        for page_size in page_sizes:
            async with monitor.monitor_query(f"thread_listing_paginated_{page_size}") as metrics:
                paginated_threads, total_count = await chat_thread.find_by_user_id_paginated(
                    session, test_user.id, page=1, per_page=page_size
                )

            assert len(paginated_threads) == min(page_size, 10)
            assert total_count == 10
            assert metrics["execution_time"] < 0.05  # Should be under 50ms
            print(f"Paginated listing ({page_size} per page): {metrics['execution_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_message_pagination_performance_scaling(
        self, session: Session, performance_test_data, test_user: User
    ):
        """Test message pagination performance across different thread sizes."""
        monitor = QueryPerformanceMonitor(session)

        # Test pagination on threads with different message counts
        for i, thread in enumerate(performance_test_data[:5]):  # Test first 5 threads
            message_count = (i + 1) * 50

            # Test first page
            async with monitor.monitor_query(f"message_pagination_first_{message_count}") as metrics:
                messages, total = await chat_message.find_by_thread_id_paginated(
                    session, thread.id, page=1, per_page=30
                )

            assert len(messages) == min(30, message_count)
            assert total == message_count
            assert metrics["execution_time"] < 0.1  # Should be under 100ms
            print(f"First page ({message_count} total messages): {metrics['execution_time_ms']:.2f}ms")

            # Test middle page (if enough messages)
            if message_count > 60:
                middle_page = message_count // 60  # Approximate middle
                async with monitor.monitor_query(f"message_pagination_middle_{message_count}") as metrics:
                    messages, total = await chat_message.find_by_thread_id_paginated(
                        session, thread.id, page=middle_page, per_page=30
                    )

                assert metrics["execution_time"] < 0.15  # Allow slightly more time for middle pages
                print(f"Middle page ({message_count} total messages): {metrics['execution_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_context_retrieval_performance_scaling(
        self, session: Session, performance_test_data, test_user: User
    ):
        """Test AI context retrieval performance with different conversation sizes."""
        monitor = QueryPerformanceMonitor(session)

        # Test context retrieval with different limits
        context_limits = [10, 30, 50, 100]

        for thread in performance_test_data[:3]:  # Test on threads with 50, 100, 150 messages
            for limit in context_limits:
                async with monitor.monitor_query(f"context_retrieval_{limit}") as metrics:
                    messages = await chat_message.get_recent_messages_for_context(session, thread.id, limit=limit)

                expected_count = min(limit, await chat_message.count_by_thread_id(session, thread.id))
                assert len(messages) == expected_count
                assert metrics["execution_time"] < 0.05  # Should be very fast with proper indexing
                print(f"Context retrieval (limit {limit}): {metrics['execution_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_message_creation_performance(self, session: Session, test_user: User):
        """Test performance of concurrent message creation."""
        # Create a test thread
        thread = await chat_thread.create(session, test_user.id, "Concurrent Test Thread")

        # Function to create messages concurrently
        async def create_message_batch(batch_id: int, batch_size: int = 10):
            tasks = []
            for i in range(batch_size):
                role = "user" if i % 2 == 0 else "assistant"
                content = f"Concurrent message {batch_id}-{i + 1}"
                task = chat_message.create(session, thread.id, role, content)
                tasks.append(task)

            return await asyncio.gather(*tasks)

        # Test concurrent creation
        start_time = time.time()

        # Create 5 batches of 10 messages each concurrently
        batch_tasks = [create_message_batch(i) for i in range(5)]
        results = await asyncio.gather(*batch_tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all messages were created
        total_messages = sum(len(batch) for batch in results)
        assert total_messages == 50

        # Should complete in reasonable time
        assert total_time < 2.0  # Should be under 2 seconds
        print(f"Concurrent message creation (50 messages): {total_time:.3f}s")

        # Verify message count
        final_count = await chat_message.count_by_thread_id(session, thread.id)
        assert final_count == 50

        # Cleanup
        await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)

    @pytest.mark.asyncio
    async def test_api_endpoint_performance_under_load(self, client: TestClient, session: Session, test_user: User):
        """Test API endpoint performance under simulated load."""
        # Mock AI Hub for consistent performance
        with patch("app.services.chat_service.AIHub") as mock_ai_hub_class:
            mock_ai_hub = AsyncMock()
            mock_ai_hub.process_chat_message.return_value = "Performance test response"
            mock_ai_hub_class.return_value = mock_ai_hub

            # Create test thread
            response = client.post("/api/chat/threads", json={"title": "Load Test Thread"})
            assert response.status_code == 201
            thread_uuid = response.json()["uuid"]

            # Test thread listing performance
            start_time = time.time()
            for _ in range(10):
                response = client.get("/api/chat/threads")
                assert response.status_code == 200
            listing_time = time.time() - start_time
            print(f"Thread listing (10 requests): {listing_time:.3f}s avg: {listing_time / 10:.3f}s")

            # Test message sending performance
            start_time = time.time()
            for i in range(10):
                response = client.post(
                    f"/api/chat/threads/{thread_uuid}/messages", json={"content": f"Load test message {i + 1}"}
                )
                assert response.status_code == 201
            sending_time = time.time() - start_time
            print(f"Message sending (10 requests): {sending_time:.3f}s avg: {sending_time / 10:.3f}s")

            # Test thread retrieval with messages performance
            start_time = time.time()
            for _ in range(10):
                response = client.get(f"/api/chat/threads/{thread_uuid}")
                assert response.status_code == 200
            retrieval_time = time.time() - start_time
            print(f"Thread retrieval (10 requests): {retrieval_time:.3f}s avg: {retrieval_time / 10:.3f}s")

            # Performance assertions
            assert listing_time / 10 < 0.1  # Average under 100ms per request
            assert sending_time / 10 < 0.5  # Average under 500ms per request (includes AI processing)
            assert retrieval_time / 10 < 0.2  # Average under 200ms per request

            # Cleanup
            response = client.delete(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200

    def test_concurrent_api_requests_performance(self, client: TestClient, session: Session, test_user: User):
        """Test API performance under concurrent requests."""
        # Mock AI Hub
        with patch("app.services.chat_service.AIHub") as mock_ai_hub_class:
            mock_ai_hub = AsyncMock()
            mock_ai_hub.process_chat_message.return_value = "Concurrent response"
            mock_ai_hub_class.return_value = mock_ai_hub

            # Create test thread
            response = client.post("/api/chat/threads", json={"title": "Concurrent Test"})
            thread_uuid = response.json()["uuid"]

            def send_message(message_id):
                return client.post(
                    f"/api/chat/threads/{thread_uuid}/messages", json={"content": f"Concurrent message {message_id}"}
                )

            def get_thread():
                return client.get(f"/api/chat/threads/{thread_uuid}")

            # Test concurrent message sending
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                message_futures = [executor.submit(send_message, i) for i in range(10)]
                message_responses = [future.result() for future in message_futures]
            message_time = time.time() - start_time

            # All requests should succeed
            for response in message_responses:
                assert response.status_code == 201

            print(f"Concurrent message sending (10 requests, 5 workers): {message_time:.3f}s")

            # Test concurrent thread retrieval
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                retrieval_futures = [executor.submit(get_thread) for _ in range(10)]
                retrieval_responses = [future.result() for future in retrieval_futures]
            retrieval_time = time.time() - start_time

            # All requests should succeed
            for response in retrieval_responses:
                assert response.status_code == 200

            print(f"Concurrent thread retrieval (10 requests, 5 workers): {retrieval_time:.3f}s")

            # Performance assertions
            assert message_time < 5.0  # Should complete within 5 seconds
            assert retrieval_time < 2.0  # Should complete within 2 seconds

            # Cleanup
            response = client.delete(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_conversations(self, session: Session, test_user: User):
        """Test memory usage patterns with large conversations."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create thread with large conversation
        thread = await chat_thread.create(session, test_user.id, "Memory Test Thread")

        # Add many messages
        batch_size = 100
        for batch in range(10):  # 1000 messages total
            messages_data = []
            for i in range(batch_size):
                role = "user" if i % 2 == 0 else "assistant"
                content = f"Memory test message {batch * batch_size + i + 1} " + "x" * 100  # Longer content
                messages_data.append({"thread_id": thread.id, "role": role, "content": content})

            await chat_message.create_batch(session, messages_data)

            # Check memory usage periodically
            if batch % 3 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                print(
                    f"Memory usage after {(batch + 1) * batch_size} messages: {current_memory:.1f}MB (+{memory_increase:.1f}MB)"
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory

        print(f"Total memory increase: {total_memory_increase:.1f}MB for 1000 messages")

        # Memory increase should be reasonable (less than 100MB for 1000 messages)
        assert total_memory_increase < 100

        # Test retrieval performance with large conversation
        start_time = time.time()
        messages = await chat_message.get_recent_messages_for_context(session, thread.id, limit=30)
        retrieval_time = time.time() - start_time

        assert len(messages) == 30
        assert retrieval_time < 0.1  # Should still be fast

        # Cleanup
        await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)

    @pytest.mark.asyncio
    async def test_database_query_optimization_verification(
        self, session: Session, performance_test_data, test_user: User
    ):
        """Verify that database queries are properly optimized."""
        QueryPerformanceMonitor(session)

        # Test various query patterns that should use indexes
        test_queries = [
            ("thread_by_user", lambda: chat_thread.find_by_user_id(session, test_user.id)),
            ("thread_by_uuid", lambda: chat_thread.find_by_uuid(session, performance_test_data[0].uuid, test_user.id)),
            (
                "messages_paginated",
                lambda: chat_message.find_by_thread_id_paginated(session, performance_test_data[0].id, 1, 30),
            ),
            (
                "messages_context",
                lambda: chat_message.get_recent_messages_for_context(session, performance_test_data[0].id, 30),
            ),
            ("message_count", lambda: chat_message.count_by_thread_id(session, performance_test_data[0].id)),
        ]

        for query_name, query_func in test_queries:
            # Benchmark each query
            benchmark_results = await benchmark_query(session, lambda s, func=query_func: func(), iterations=5)

            print(
                f"{query_name}: avg={benchmark_results['avg_time_ms']:.2f}ms, "
                f"min={benchmark_results['min_time_ms']:.2f}ms, "
                f"max={benchmark_results['max_time_ms']:.2f}ms"
            )

            # All queries should be consistently fast
            assert benchmark_results["max_time"] < 0.1  # Even worst case under 100ms
            assert benchmark_results["avg_time"] < 0.05  # Average under 50ms

    @pytest.mark.asyncio
    async def test_pagination_efficiency_analysis(self, session: Session, performance_test_data, test_user: User):
        """Analyze pagination efficiency across different scenarios."""
        from tests.utils.performance import PaginationOptimizer

        # Test pagination on largest thread (500 messages)
        largest_thread = performance_test_data[-1]
        total_messages = await chat_message.count_by_thread_id(session, largest_thread.id)

        # Test different pagination scenarios
        scenarios = [
            (1, 30),  # First page
            (5, 30),  # Early page
            (10, 30),  # Middle page
            (16, 30),  # Late page (near end)
        ]

        for page, per_page in scenarios:
            start_time = time.time()
            messages, total = await chat_message.find_by_thread_id_paginated(session, largest_thread.id, page, per_page)
            query_time = time.time() - start_time

            # Analyze pagination strategy
            strategy = PaginationOptimizer.suggest_pagination_strategy(page, per_page, total_messages)

            print(
                f"Page {page}: {query_time * 1000:.2f}ms, "
                f"efficiency={strategy['efficiency_score']:.2f}, "
                f"recommended={strategy['recommended_strategy']}"
            )

            # Performance should degrade gracefully
            if strategy["performance_warning"]:
                assert query_time < 0.2  # Allow more time for inefficient pages
            else:
                assert query_time < 0.1  # Normal pages should be fast

    @pytest.mark.asyncio
    async def test_cleanup_performance(self, session: Session, test_user: User):
        """Test performance of cleanup operations."""
        # Create test data for cleanup
        threads_to_cleanup = []
        for i in range(5):
            thread = await chat_thread.create(session, test_user.id, f"Cleanup Test {i}")
            threads_to_cleanup.append(thread)

            # Add messages to each thread
            for j in range(20):
                role = "user" if j % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {j}")

        # Test individual thread deletion performance
        start_time = time.time()
        for thread in threads_to_cleanup[:3]:
            success = await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)
            assert success
        individual_deletion_time = time.time() - start_time

        print(f"Individual thread deletion (3 threads): {individual_deletion_time:.3f}s")
        assert individual_deletion_time < 1.0  # Should be under 1 second

        # Test batch cleanup (remaining threads)
        start_time = time.time()
        for thread in threads_to_cleanup[3:]:
            await chat_thread.delete_by_uuid(session, thread.uuid, test_user.id)
        batch_deletion_time = time.time() - start_time

        print(f"Batch thread deletion (2 threads): {batch_deletion_time:.3f}s")
        assert batch_deletion_time < 0.5  # Should be under 0.5 seconds
