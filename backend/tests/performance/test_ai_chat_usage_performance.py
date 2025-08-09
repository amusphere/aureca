"""Performance tests for AI Chat usage system."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.constants.plan_limits import PlanLimits
from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import User
from app.services.ai_chat_usage_service import AIChatUsageService
from app.services.auth import auth_user
from main import app


class TestAIChatUsagePerformance:
    """Performance tests for AI Chat usage system."""

    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock dependencies to ensure consistent test behavior."""
        # Mock ClerkService
        with patch("app.services.ai_chat_usage_service.get_clerk_service") as mock_get_clerk_service:
            from unittest.mock import AsyncMock

            mock_clerk_service = AsyncMock()
            mock_get_clerk_service.return_value = mock_clerk_service

            # Default to standard plan for most tests
            mock_clerk_service.get_user_plan.return_value = "standard"

            yield {
                "mock_clerk_service": mock_clerk_service,
            }

    def test_plan_limits_constant_access_performance(self):
        """Test that PlanLimits constant access is fast."""
        # Measure time for 10000 constant accesses
        start_time = time.time()

        for _ in range(10000):
            limit = PlanLimits.get_limit("standard")
            assert limit == 10

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 0.1 seconds (very fast)
        assert duration < 0.1, f"Constant access took {duration:.4f}s, expected < 0.1s"

        # Test different plan names
        start_time = time.time()

        for _ in range(5000):
            PlanLimits.get_limit("free")
            PlanLimits.get_limit("standard")

        end_time = time.time()
        duration = end_time - start_time

        # Should still be very fast
        assert duration < 0.05, f"Mixed constant access took {duration:.4f}s, expected < 0.05s"

    def test_database_query_performance(self, session: Session, test_user: User):
        """Test database query performance for usage checks."""
        current_date = "2023-01-01"

        # Create some usage data
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 5)

        # Measure time for 100 database queries
        start_time = time.time()

        for _ in range(100):
            usage_count = AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            assert usage_count == 5

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 1 second
        assert duration < 1.0, f"100 DB queries took {duration:.4f}s, expected < 1.0s"

        # Average per query should be less than 10ms
        avg_per_query = duration / 100
        assert avg_per_query < 0.01, f"Average query time {avg_per_query:.4f}s, expected < 0.01s"

    async def test_service_layer_performance(self, session: Session, test_user: User):
        """Test service layer performance for usage operations."""
        current_date = "2023-01-01"
        usage_service = AIChatUsageService(session)

        # Measure time for usage stats retrieval
        with patch.object(usage_service, "_get_current_date", return_value=current_date):
            start_time = time.time()

            for _ in range(50):
                stats = await usage_service.get_usage_stats(test_user)
                assert "remaining_count" in stats

            end_time = time.time()
            duration = end_time - start_time

            # Should complete in less than 2 seconds
            assert duration < 2.0, f"50 service calls took {duration:.4f}s, expected < 2.0s"

            # Average per call should be less than 40ms
            avg_per_call = duration / 50
            assert avg_per_call < 0.04, f"Average service call time {avg_per_call:.4f}s, expected < 0.04s"

    def test_api_endpoint_performance(self, client: TestClient, session: Session, test_user: User):
        """Test API endpoint performance."""
        current_date = "2023-01-01"

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Measure time for 20 API calls
                start_time = time.time()

                for _ in range(20):
                    response = client.get("/api/ai/usage")
                    assert response.status_code == 200

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in less than 5 seconds
                assert duration < 5.0, f"20 API calls took {duration:.4f}s, expected < 5.0s"

                # Average per call should be less than 250ms
                avg_per_call = duration / 20
                assert avg_per_call < 0.25, f"Average API call time {avg_per_call:.4f}s, expected < 0.25s"
        finally:
            app.dependency_overrides.clear()

    def test_concurrent_usage_checks_performance(self, client: TestClient, session: Session, test_user: User):
        """Test performance under concurrent load."""
        current_date = "2023-01-01"

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):

                def make_request():
                    response = client.get("/api/ai/usage")
                    return response.status_code == 200

                # Test with 10 concurrent requests
                start_time = time.time()

                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(make_request) for _ in range(10)]
                    results = [future.result() for future in futures]

                end_time = time.time()
                duration = end_time - start_time

                # All requests should succeed
                assert all(results), "Some concurrent requests failed"

                # Should complete in less than 3 seconds
                assert duration < 3.0, f"10 concurrent requests took {duration:.4f}s, expected < 3.0s"
        finally:
            app.dependency_overrides.clear()

    def test_usage_increment_performance(self, client: TestClient, session: Session, test_user: User):
        """Test performance of usage increment operations."""
        current_date = "2023-01-01"

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Measure time for 10 increment operations
                start_time = time.time()

                for i in range(10):
                    response = client.post("/api/ai/usage/increment")
                    if i < 9:  # First 9 should succeed
                        assert response.status_code == 200
                    # 10th might hit limit depending on timing

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in less than 3 seconds
                assert duration < 3.0, f"10 increment operations took {duration:.4f}s, expected < 3.0s"

                # Average per operation should be less than 300ms
                avg_per_operation = duration / 10
                assert avg_per_operation < 0.3, f"Average increment time {avg_per_operation:.4f}s, expected < 0.3s"
        finally:
            app.dependency_overrides.clear()

    async def test_clerk_api_mock_performance(self, session: Session, test_user: User, mock_dependencies):
        """Test performance with Clerk API mocking."""
        usage_service = AIChatUsageService(session)

        # Measure time for 100 plan retrievals
        start_time = time.time()

        for _ in range(100):
            plan = await usage_service.get_user_plan(test_user)
            assert plan == "standard"

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 1 second (mocked calls are fast)
        assert duration < 1.0, f"100 mocked Clerk API calls took {duration:.4f}s, expected < 1.0s"

        # Average per call should be less than 10ms
        avg_per_call = duration / 100
        assert avg_per_call < 0.01, f"Average mocked API call time {avg_per_call:.4f}s, expected < 0.01s"

    def test_memory_usage_stability(self, session: Session, test_user: User):
        """Test that memory usage remains stable under load."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        usage_service = AIChatUsageService(session)
        current_date = "2023-01-01"

        # Perform many operations
        with patch.object(usage_service, "_get_current_date", return_value=current_date):

            async def run_operations():
                for _ in range(1000):
                    await usage_service.get_usage_stats(test_user)
                    if _ % 100 == 0:
                        gc.collect()  # Force garbage collection

            # Run the operations
            asyncio.run(run_operations())

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB, expected < 50MB"

    def test_database_connection_efficiency(self, session: Session, test_user: User):
        """Test database connection efficiency."""
        current_date = "2023-01-01"

        # Create initial usage
        AIChatUsageRepository.create_daily_usage(session, test_user.id, current_date, 0)

        # Measure time for mixed operations
        start_time = time.time()

        for i in range(50):
            # Mix of read and write operations
            if i % 2 == 0:
                AIChatUsageRepository.get_current_usage_count(session, test_user.id, current_date)
            else:
                AIChatUsageRepository.increment_usage_count(session, test_user.id, current_date)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 2 seconds
        assert duration < 2.0, f"50 mixed DB operations took {duration:.4f}s, expected < 2.0s"

    async def test_error_handling_performance(self, session: Session, test_user: User):
        """Test that error handling doesn't significantly impact performance."""
        usage_service = AIChatUsageService(session)

        # Measure time for operations that will cause errors
        start_time = time.time()

        for _ in range(20):
            try:
                # This should raise an exception due to invalid date
                with patch.object(usage_service, "_get_current_date", side_effect=Exception("Test error")):
                    await usage_service.get_usage_stats(test_user)
            except Exception:
                pass  # Expected

        end_time = time.time()
        duration = end_time - start_time

        # Error handling should not be significantly slower
        assert duration < 1.0, f"20 error operations took {duration:.4f}s, expected < 1.0s"

    def test_plan_validation_performance(self):
        """Test performance of plan validation operations."""
        # Test valid plan checks
        start_time = time.time()

        for _ in range(10000):
            assert PlanLimits.is_valid_plan("standard") is True
            assert PlanLimits.is_valid_plan("free") is True
            assert PlanLimits.is_valid_plan("invalid") is False

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast
        assert duration < 0.1, f"30000 plan validations took {duration:.4f}s, expected < 0.1s"

    def test_response_serialization_performance(self, client: TestClient, session: Session, test_user: User):
        """Test JSON response serialization performance."""
        current_date = "2023-01-01"

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            with patch(
                "app.services.ai_chat_usage_service.AIChatUsageService._get_current_date",
                return_value=current_date,
            ):
                # Measure time for response parsing
                responses = []
                start_time = time.time()

                for _ in range(50):
                    response = client.get("/api/ai/usage")
                    assert response.status_code == 200
                    data = response.json()  # This tests serialization performance
                    responses.append(data)

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in less than 2 seconds
                assert duration < 2.0, f"50 response serializations took {duration:.4f}s, expected < 2.0s"

                # Verify all responses have correct structure
                for data in responses:
                    assert "remaining_count" in data
                    assert "daily_limit" in data
                    assert "plan_name" in data
        finally:
            app.dependency_overrides.clear()
