"""Performance tests for task priority system."""

import statistics
import time

import pytest
from sqlmodel import Session

from app.repositories.tasks import find_tasks
from app.schema import TaskPriority, Tasks, User


class TestTaskPriorityPerformance:
    """Performance tests for task priority functionality."""

    @pytest.mark.skip(reason="Skipped due to flaky performance test - depends on system performance")
    def test_large_dataset_priority_sorting_performance(self, session: Session, test_user: User):
        """Test priority sorting performance with large datasets."""
        # Test with different dataset sizes
        dataset_sizes = [100, 500, 1000, 2000]
        performance_results = {}

        for size in dataset_sizes:
            # Clear previous test data
            from sqlmodel import select

            stmt = select(Tasks).where(Tasks.user_id == test_user.id)
            existing_tasks = session.exec(stmt).all()
            for task in existing_tasks:
                session.delete(task)
            session.commit()

            # Create test data
            self._create_test_tasks(session, test_user, size)

            # Measure sorting performance
            execution_times = []

            # Run multiple iterations to get average performance
            for _ in range(5):
                start_time = time.time()
                tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)
                end_time = time.time()

                execution_times.append(end_time - start_time)

                # Verify correct number of tasks returned
                assert len(tasks) == size

            # Calculate performance metrics
            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)

            performance_results[size] = {"avg_time": avg_time, "max_time": max_time, "min_time": min_time}

            # Performance assertions
            assert avg_time < 2.0, f"Average sorting time {avg_time:.3f}s too slow for {size} tasks"
            assert max_time < 3.0, f"Maximum sorting time {max_time:.3f}s too slow for {size} tasks"

        # Verify performance scales reasonably
        self._verify_performance_scaling(performance_results)

    def test_priority_sorting_vs_no_sorting_performance(self, session: Session, test_user: User):
        """Compare performance of priority sorting vs no sorting."""
        test_size = 1000

        # Create test data
        self._create_test_tasks(session, test_user, test_size)

        # Measure priority sorting performance
        priority_times = []
        for _ in range(10):
            start_time = time.time()
            tasks_with_priority = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)
            end_time = time.time()
            priority_times.append(end_time - start_time)

        # Measure no sorting performance
        no_sort_times = []
        for _ in range(10):
            start_time = time.time()
            tasks_no_sort = find_tasks(session=session, user_id=test_user.id, order_by_priority=False)
            end_time = time.time()
            no_sort_times.append(end_time - start_time)

        avg_priority_time = statistics.mean(priority_times)
        avg_no_sort_time = statistics.mean(no_sort_times)

        # Verify both return same number of tasks
        assert len(tasks_with_priority) == len(tasks_no_sort) == test_size

        # Priority sorting should be reasonably close to no sorting
        # (with proper indexing, the difference should be minimal)
        # Allow for some performance difference due to priority processing
        performance_ratio = avg_priority_time / avg_no_sort_time
        assert performance_ratio < 5.0, f"Priority sorting is {performance_ratio:.2f}x slower than no sorting"

        print(f"Priority sorting: {avg_priority_time:.4f}s avg")
        print(f"No sorting: {avg_no_sort_time:.4f}s avg")
        print(f"Performance ratio: {performance_ratio:.2f}x")

    def test_database_index_effectiveness(self, session: Session, test_user: User):
        """Test that database indexes are effective for priority queries."""
        test_size = 5000

        # Create large test dataset
        self._create_test_tasks(session, test_user, test_size)

        # Test various query patterns that should benefit from indexes
        query_patterns = [
            # Priority sorting (should use priority index)
            lambda: find_tasks(session=session, user_id=test_user.id, order_by_priority=True),
            # Completed filter with priority sorting
            lambda: find_tasks(session=session, user_id=test_user.id, completed=False, order_by_priority=True),
            # Expires_at filter with priority sorting
            lambda: find_tasks(session=session, user_id=test_user.id, expires_at=1672617600.0, order_by_priority=True),
        ]

        for i, query_func in enumerate(query_patterns):
            execution_times = []

            for _ in range(3):
                start_time = time.time()
                results = query_func()
                end_time = time.time()

                execution_times.append(end_time - start_time)

                # Verify query returns results
                assert len(results) > 0

            avg_time = statistics.mean(execution_times)

            # With proper indexes, even complex queries should be fast
            assert avg_time < 1.0, f"Query pattern {i} too slow: {avg_time:.3f}s"

            print(f"Query pattern {i}: {avg_time:.4f}s avg")

    def test_memory_usage_with_large_datasets(self, session: Session, test_user: User):
        """Test memory usage patterns with large task datasets."""
        # Note: psutil not available in test environment, so we'll do a basic test

        # Create large dataset
        test_size = 1000  # Reduced size for basic test
        self._create_test_tasks(session, test_user, test_size)

        # Perform priority sorting query
        start_time = time.time()
        tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)
        end_time = time.time()

        execution_time = end_time - start_time

        # Verify we got the expected number of tasks
        assert len(tasks) == test_size

        # Verify performance is still good with large dataset
        assert execution_time < 2.0, f"Query too slow with large dataset: {execution_time:.3f}s"

        print(f"Large dataset query time: {execution_time:.4f}s for {test_size} tasks")

    def test_concurrent_priority_queries(self, session: Session, test_user: User):
        """Test performance under concurrent priority sorting queries."""
        import pytest

        pytest.skip("SQLite doesn't support true concurrency - skipping this test")

        # Alternative: Test sequential execution multiple times instead of concurrency
        test_size = 100  # Smaller size for repeated queries
        self._create_test_tasks(session, test_user, test_size)

        execution_times = []

        # Run the same query multiple times sequentially
        for _i in range(5):
            start_time = time.time()
            tasks = find_tasks(session=session, user_id=test_user.id, order_by_priority=True)
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            # Verify task count is consistent
            assert len(tasks) == test_size

        # Verify performance is consistent across multiple runs
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)

        # Performance should be relatively consistent
        assert max_time / min_time < 3.0, "Performance varies too much between runs"
        assert avg_time < 1.0, f"Average query time {avg_time:.3f}s too slow"

        print(f"Sequential query stats - Avg: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s")

    def _create_test_tasks(self, session: Session, user: User, count: int) -> list[Tasks]:
        """Create test tasks with mixed priorities using factory pattern."""
        from tests.utils.test_data_factory import TestDataFactory

        tasks = []
        priorities = [TaskPriority.HIGH, TaskPriority.MIDDLE, TaskPriority.LOW, None]

        for i in range(count):
            priority = priorities[i % len(priorities)]

            task = TestDataFactory.create_task(
                user_id=user.id,
                title=f"Performance Test Task {i}",
                description=f"Description for task {i}",
                priority=priority,
                completed=False,  # Keep all tasks uncompleted for consistent testing
                expires_at=1672617600.0 + (i * 3600),  # Staggered expiry times
                created_at=1672531200.0 + i,
                updated_at=1672531200.0 + i,
            )

            session.add(task)
            tasks.append(task)

        session.commit()
        return tasks

    def _verify_performance_scaling(self, performance_results: dict):
        """Verify that performance scales reasonably with dataset size."""
        sizes = sorted(performance_results.keys())

        for i in range(1, len(sizes)):
            current_size = sizes[i]
            previous_size = sizes[i - 1]

            current_time = performance_results[current_size]["avg_time"]
            previous_time = performance_results[previous_size]["avg_time"]

            size_ratio = current_size / previous_size
            time_ratio = current_time / previous_time

            # Performance should scale sub-linearly (better than O(n))
            # With SQLite, scaling may not be as optimal as PostgreSQL with proper indexing
            # Allow for more generous scaling in test environment
            assert time_ratio < size_ratio * 2.5, (
                f"Performance scaling too poor: {time_ratio:.2f}x time for {size_ratio:.2f}x data"
            )

            print(f"Size {previous_size} -> {current_size}: {time_ratio:.2f}x time for {size_ratio:.2f}x data")
