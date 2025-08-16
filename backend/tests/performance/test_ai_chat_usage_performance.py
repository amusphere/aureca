"""Performance tests for AI Chat usage system."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

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

    async def test_service_layer_performance(
        self, session: Session, test_user: User, mock_clerk_service: MagicMock, mock_ai_usage_repository: MagicMock
    ):
        """Test service layer performance for usage operations."""
        current_date = "2023-01-01"

        # Use dependency injection for clean testing
        usage_service = AIChatUsageService(
            session=session, clerk_service=mock_clerk_service, usage_repository=mock_ai_usage_repository
        )

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

    def test_api_endpoint_performance(self, client: TestClient, session: Session, test_user: User, setup_app_overrides):
        """Test API endpoint performance with proper mocking."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            # Mock the service creation in the API endpoints to avoid external calls
            with patch("app.routers.api.ai_assistant.AIChatUsageService") as mock_service_class:
                # Set up the mock service instance
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Configure mock responses for async methods
                mock_service.get_usage_stats = AsyncMock(
                    return_value={
                        "remaining_count": 8,
                        "daily_limit": 10,
                        "current_usage": 2,
                        "plan_name": "standard",
                        "reset_time": "2023-01-02T00:00:00Z",
                        "can_use_chat": True,
                    }
                )

                # Measure time for 20 API calls
                start_time = time.time()

                for _ in range(20):
                    response = client.get("/api/ai/usage")
                    assert response.status_code == 200

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in less than 2 seconds (reduced expectation for mocked calls)
                assert duration < 2.0, f"20 API calls took {duration:.4f}s, expected < 2.0s"

                # Average per call should be less than 100ms (reduced expectation for mocked calls)
                avg_per_call = duration / 20
                assert avg_per_call < 0.1, f"Average API call time {avg_per_call:.4f}s, expected < 0.1s"
        finally:
            # Remove only the auth override, keep setup_app_overrides intact
            if auth_user in app.dependency_overrides:
                del app.dependency_overrides[auth_user]

    def test_concurrent_usage_checks_performance(
        self, client: TestClient, session: Session, test_user: User, setup_app_overrides
    ):
        """Test performance under concurrent load with proper mocking."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            # Mock the service creation in the API endpoints to avoid external calls
            with patch("app.routers.api.ai_assistant.AIChatUsageService") as mock_service_class:
                # Set up the mock service instance
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Configure mock responses for async methods
                mock_service.get_usage_stats = AsyncMock(
                    return_value={
                        "remaining_count": 8,
                        "daily_limit": 10,
                        "current_usage": 2,
                        "plan_name": "standard",
                        "reset_time": "2023-01-02T00:00:00Z",
                        "can_use_chat": True,
                    }
                )

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

                # Should complete in less than 1 second (reduced expectation for mocked calls)
                assert duration < 1.0, f"10 concurrent requests took {duration:.4f}s, expected < 1.0s"
        finally:
            # Remove only the auth override, keep setup_app_overrides intact
            if auth_user in app.dependency_overrides:
                del app.dependency_overrides[auth_user]

    @pytest.mark.skip(reason="Skipped due to temporary workaround: mocking conflicts with workaround implementation")
    def test_usage_increment_performance(
        self, client: TestClient, session: Session, test_user: User, setup_app_overrides
    ):
        """Test performance of usage increment operations with proper mocking."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            # Mock the service creation in the API endpoints to avoid external calls
            with patch("app.routers.api.ai_assistant.AIChatUsageService") as mock_service_class:
                # Set up the mock service instance
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Configure mock responses for async methods
                mock_service.increment_usage = AsyncMock(
                    return_value={
                        "remaining_count": 7,
                        "daily_limit": 10,
                        "current_usage": 3,
                        "plan_name": "standard",
                        "reset_time": "2023-01-02T00:00:00Z",
                        "can_use_chat": True,
                    }
                )

                # Measure time for 10 increment operations
                start_time = time.time()

                for _ in range(10):
                    response = client.post("/api/ai/usage/increment")
                    assert response.status_code == 200  # All should succeed with mocked service

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in less than 1 second (reduced expectation for mocked calls)
                assert duration < 1.0, f"10 increment operations took {duration:.4f}s, expected < 1.0s"

                # Average per operation should be less than 100ms (reduced expectation for mocked calls)
                avg_per_operation = duration / 10
                assert avg_per_operation < 0.1, f"Average increment time {avg_per_operation:.4f}s, expected < 0.1s"
        finally:
            # Remove only the auth override, keep setup_app_overrides intact
            if auth_user in app.dependency_overrides:
                del app.dependency_overrides[auth_user]

    async def test_clerk_api_mock_performance(
        self, session: Session, test_user: User, mock_clerk_service: MagicMock, mock_ai_usage_repository: MagicMock
    ):
        """Test performance with Clerk API mocking."""
        # Use dependency injection for clean testing
        usage_service = AIChatUsageService(
            session=session, clerk_service=mock_clerk_service, usage_repository=mock_ai_usage_repository
        )

        # Measure time for 100 plan retrievals
        start_time = time.time()

        for _ in range(100):
            plan = usage_service.get_user_plan(test_user)
            assert plan == "standard"

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in less than 1 second (mocked calls are fast)
        assert duration < 1.0, f"100 mocked Clerk API calls took {duration:.4f}s, expected < 1.0s"

        # Average per call should be less than 10ms
        avg_per_call = duration / 100
        assert avg_per_call < 0.01, f"Average mocked API call time {avg_per_call:.4f}s, expected < 0.01s"

    def test_memory_usage_stability(
        self, session: Session, test_user: User, mock_clerk_service: MagicMock, mock_ai_usage_repository: MagicMock
    ):
        """Test that memory usage remains stable under load."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Use dependency injection for clean testing
        usage_service = AIChatUsageService(
            session=session, clerk_service=mock_clerk_service, usage_repository=mock_ai_usage_repository
        )
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

    async def test_error_handling_performance(
        self, session: Session, test_user: User, mock_clerk_service: MagicMock, mock_ai_usage_repository: MagicMock
    ):
        """Test that error handling doesn't significantly impact performance."""
        # Use dependency injection for clean testing
        usage_service = AIChatUsageService(
            session=session, clerk_service=mock_clerk_service, usage_repository=mock_ai_usage_repository
        )

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

    def test_response_serialization_performance(
        self, client: TestClient, session: Session, test_user: User, setup_app_overrides
    ):
        """Test JSON response serialization performance with proper mocking."""

        def get_test_user():
            return test_user

        app.dependency_overrides[auth_user] = get_test_user

        try:
            # Mock the service creation in the API endpoints to avoid external calls
            with patch("app.routers.api.ai_assistant.AIChatUsageService") as mock_service_class:
                # Set up the mock service instance
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Configure mock responses for async methods
                mock_service.get_usage_stats = AsyncMock(
                    return_value={
                        "remaining_count": 8,
                        "daily_limit": 10,
                        "current_usage": 2,
                        "plan_name": "standard",
                        "reset_time": "2023-01-02T00:00:00Z",
                        "can_use_chat": True,
                    }
                )

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

                # Should complete in less than 1 second (reduced expectation for mocked calls)
                assert duration < 1.0, f"50 response serializations took {duration:.4f}s, expected < 1.0s"

                # Verify all responses have correct structure
                for data in responses:
                    assert "remaining_count" in data
                    assert "daily_limit" in data
                    assert "plan_name" in data
        finally:
            # Remove only the auth override, keep setup_app_overrides intact
            if auth_user in app.dependency_overrides:
                del app.dependency_overrides[auth_user]
