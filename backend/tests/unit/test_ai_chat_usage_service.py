"""Unit tests for AI chat usage service functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from sqlmodel import Session

from app.schema import AIChatUsage, User
from app.services.ai_chat_usage_service import AIChatUsageService


class TestAIChatUsageService:
    """Unit tests for AI chat usage service functionality."""

    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock dependencies to ensure consistent test behavior."""
        # Mock PlanLimits.get_limit
        with patch("app.services.ai_chat_usage_service.PlanLimits.get_limit") as mock_get_limit:

            def get_limit_side_effect(plan_name):
                limits = {
                    "free": 0,
                    "standard": 10,
                }
                return limits.get(plan_name, 0)

            mock_get_limit.side_effect = get_limit_side_effect

            # Mock ClerkService
            with patch("app.services.ai_chat_usage_service.ClerkService") as mock_clerk_service_class:
                mock_clerk_service = AsyncMock()
                mock_clerk_service_class.return_value = mock_clerk_service

                # Default to standard plan for most tests
                mock_clerk_service.get_user_plan.return_value = "standard"

                yield {
                    "mock_get_limit": mock_get_limit,
                    "mock_clerk_service": mock_clerk_service,
                    "mock_clerk_service_class": mock_clerk_service_class,
                }

    @pytest.fixture
    def service(self, session: Session):
        """Create AIChatUsageService instance with test session."""
        return AIChatUsageService(session=session)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        return User(
            id=1,
            clerk_sub="test_user_123",
            email="test@example.com",
            created_at=1672531200.0,
        )

    async def test_get_user_plan_standard(self, service: AIChatUsageService, mock_user: User, mock_dependencies):
        """Test get_user_plan returns standard plan from Clerk."""
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        plan = await service.get_user_plan(mock_user)
        assert plan == "standard"
        mock_dependencies["mock_clerk_service"].get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    async def test_get_user_plan_free(self, service: AIChatUsageService, mock_user: User, mock_dependencies):
        """Test get_user_plan returns free plan from Clerk."""
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

        plan = await service.get_user_plan(mock_user)
        assert plan == "free"
        mock_dependencies["mock_clerk_service"].get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    def test_get_daily_limit_free_plan(self, service: AIChatUsageService):
        """Test get_daily_limit for free plan."""
        limit = service.get_daily_limit("free")
        assert limit == 0

    def test_get_daily_limit_standard_plan(self, service: AIChatUsageService):
        """Test get_daily_limit for standard plan."""
        limit = service.get_daily_limit("standard")
        assert limit == 10

    def test_get_daily_limit_unknown_plan(self, service: AIChatUsageService):
        """Test get_daily_limit for unknown plan defaults to free."""
        limit = service.get_daily_limit("unknown_plan")
        assert limit == 0

    @patch("app.services.ai_chat_usage_service.datetime")
    def test_get_current_date(self, mock_datetime, service: AIChatUsageService):
        """Test _get_current_date returns correct format."""
        # Mock current time
        mock_now = datetime(2023, 1, 15, 14, 30, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        date = service._get_current_date()
        assert date == "2023-01-15"

    @patch("app.services.ai_chat_usage_service.datetime")
    def test_get_reset_time(self, mock_datetime, service: AIChatUsageService):
        """Test _get_reset_time returns correct next midnight."""
        # Mock current time: 2023-01-15 14:30:00 UTC
        mock_now = datetime(2023, 1, 15, 14, 30, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        reset_time = service._get_reset_time()

        # Should return next midnight: 2023-01-16 00:00:00 UTC
        expected_reset = datetime(2023, 1, 16, 0, 0, 0, tzinfo=UTC)
        assert reset_time == expected_reset.isoformat()

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_no_usage(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test get_usage_stats for standard plan user with no usage."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 0
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 10
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 0
        assert stats["reset_time"] == "2023-01-16T00:00:00+00:00"
        assert stats["can_use_chat"] is True

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_partial_usage(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test get_usage_stats for standard plan user with partial usage."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 7
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 3
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 7
        assert stats["can_use_chat"] is True

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_limit_reached(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test get_usage_stats for standard plan user who reached limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 10
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 10
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_over_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test get_usage_stats for standard plan user who exceeded limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 15
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0  # Should not go negative
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 15
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_free_plan_no_access(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test get_usage_stats for free plan user (no access)."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 0
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0
        assert stats["daily_limit"] == 0
        assert stats["current_usage"] == 0
        assert stats["can_use_chat"] is False

    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_check_usage_limit_free_plan_restriction(
        self,
        mock_get_stats,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test check_usage_limit raises exception for free plan."""
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "free"
        mock_get_stats.return_value = {
            "remaining_count": 0,
            "daily_limit": 0,
            "current_usage": 0,
            "reset_time": "2023-01-16T00:00:00+00:00",
            "can_use_chat": False,
        }

        with pytest.raises(HTTPException) as exc_info:
            await service.check_usage_limit(mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "PLAN_RESTRICTION" in str(exc_info.value.detail)

    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_check_usage_limit_standard_plan_within_limit(
        self, mock_get_stats, service: AIChatUsageService, mock_user: User
    ):
        """Test check_usage_limit passes for standard plan within limit."""
        mock_get_stats.return_value = {
            "remaining_count": 5,
            "daily_limit": 10,
            "current_usage": 5,
            "reset_time": "2023-01-16T00:00:00+00:00",
            "can_use_chat": True,
        }

        result = await service.check_usage_limit(mock_user)

        assert result["remaining_count"] == 5
        assert result["daily_limit"] == 10
        assert result["can_use_chat"] is True

    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_check_usage_limit_standard_plan_limit_exceeded(
        self, mock_get_stats, service: AIChatUsageService, mock_user: User
    ):
        """Test check_usage_limit raises exception when limit exceeded."""
        mock_get_stats.return_value = {
            "remaining_count": 0,
            "daily_limit": 10,
            "current_usage": 10,
            "reset_time": "2023-01-16T00:00:00+00:00",
            "can_use_chat": False,
        }

        with pytest.raises(HTTPException) as exc_info:
            await service.check_usage_limit(mock_user)

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "USAGE_LIMIT_EXCEEDED" in str(exc_info.value.detail)

    @patch.object(AIChatUsageService, "check_usage_limit")
    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_increment_usage_success(
        self,
        mock_get_stats,
        mock_current_date,
        mock_repo,
        mock_check_limit,
        service: AIChatUsageService,
        mock_user: User,
    ):
        """Test increment_usage successfully increments and returns updated stats."""
        mock_current_date.return_value = "2023-01-15"
        mock_check_limit.return_value = {"can_use_chat": True}
        mock_get_stats.return_value = {
            "remaining_count": 4,
            "daily_limit": 10,
            "current_usage": 6,
            "reset_time": "2023-01-16T00:00:00+00:00",
            "can_use_chat": True,
        }

        result = await service.increment_usage(mock_user)

        mock_check_limit.assert_called_once_with(mock_user)
        mock_repo.increment_daily_usage.assert_called_once_with(service.session, mock_user.id, "2023-01-15")
        assert result["remaining_count"] == 4
        assert result["current_usage"] == 6

    @patch.object(AIChatUsageService, "check_usage_limit")
    async def test_increment_usage_limit_exceeded(self, mock_check_limit, service: AIChatUsageService, mock_user: User):
        """Test increment_usage raises exception when limit check fails."""
        mock_check_limit.side_effect = HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error_code": "USAGE_LIMIT_EXCEEDED"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.increment_usage(mock_user)

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @patch.object(AIChatUsageService, "check_usage_limit")
    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_increment_usage_database_error(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        mock_check_limit,
        service: AIChatUsageService,
        mock_user: User,
    ):
        """Test increment_usage handles database errors gracefully."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_check_limit.return_value = {"can_use_chat": True}
        mock_repo.increment_daily_usage.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await service.increment_usage(mock_user)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "SYSTEM_ERROR" in str(exc_info.value.detail)

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    async def test_get_usage_history(self, mock_repo, service: AIChatUsageService, mock_user: User):
        """Test get_usage_history returns repository results."""
        mock_logs = [
            AIChatUsage(id=1, user_id=1, usage_date="2023-01-15", usage_count=5),
            AIChatUsage(id=2, user_id=1, usage_date="2023-01-14", usage_count=3),
        ]
        mock_repo.get_usage_history.return_value = mock_logs

        result = await service.get_usage_history(mock_user, limit=10)

        mock_repo.get_usage_history.assert_called_once_with(service.session, mock_user.id, 10)
        assert result == mock_logs

    async def test_clerk_service_integration(self, service: AIChatUsageService, mock_user: User, mock_dependencies):
        """Test integration with ClerkService for plan retrieval."""
        # Test that the service properly calls ClerkService
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        plan = await service.get_user_plan(mock_user)

        assert plan == "standard"
        mock_dependencies["mock_clerk_service"].get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    async def test_clerk_service_error_handling(self, service: AIChatUsageService, mock_user: User, mock_dependencies):
        """Test error handling when ClerkService fails."""
        # Mock ClerkService to raise an exception
        mock_dependencies["mock_clerk_service"].get_user_plan.side_effect = Exception("Clerk API error")

        # Should fallback to free plan
        plan = await service.get_user_plan(mock_user)

        assert plan == "free"

    # Boundary value tests
    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_exactly_at_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test boundary condition when usage is exactly at limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 10  # Exactly at limit
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_one_below_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test boundary condition when usage is one below limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 9  # One below limit
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 1
        assert stats["can_use_chat"] is True

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_one_above_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test boundary condition when usage is one above limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.return_value = 11  # One above limit
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0  # Should not go negative
        assert stats["can_use_chat"] is False

    # Edge case tests
    def test_edge_case_zero_daily_limit(self, service: AIChatUsageService):
        """Test edge case with zero daily limit (free plan)."""
        limit = service.get_daily_limit("free")
        assert limit == 0

    @patch("app.services.ai_chat_usage_service.datetime")
    def test_edge_case_date_boundary_midnight(self, mock_datetime, service: AIChatUsageService):
        """Test edge case at exactly midnight."""
        # Mock exactly midnight
        mock_now = datetime(2023, 1, 15, 0, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        date = service._get_current_date()
        reset_time = service._get_reset_time()

        assert date == "2023-01-15"
        # Next reset should be tomorrow midnight
        expected_reset = datetime(2023, 1, 16, 0, 0, 0, tzinfo=UTC)
        assert reset_time == expected_reset.isoformat()

    @patch("app.services.ai_chat_usage_service.datetime")
    def test_edge_case_date_boundary_before_midnight(self, mock_datetime, service: AIChatUsageService):
        """Test edge case just before midnight."""
        # Mock 23:59:59
        mock_now = datetime(2023, 1, 15, 23, 59, 59, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        date = service._get_current_date()
        reset_time = service._get_reset_time()

        assert date == "2023-01-15"
        # Next reset should be in 1 second
        expected_reset = datetime(2023, 1, 16, 0, 0, 0, tzinfo=UTC)
        assert reset_time == expected_reset.isoformat()

    # Error handling tests
    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_error_handling_invalid_user(self, mock_get_stats, service: AIChatUsageService):
        """Test error handling with invalid user."""
        invalid_user = User(id=None, clerk_sub="invalid")
        mock_get_stats.side_effect = Exception("Invalid user")

        with pytest.raises(Exception, match="Invalid user"):
            await service.check_usage_limit(invalid_user)

    def test_error_handling_invalid_plan_name(self, service: AIChatUsageService):
        """Test error handling with invalid plan name."""
        # Should default to free plan (0 limit)
        limit = service.get_daily_limit("")
        assert limit == 0

        limit = service.get_daily_limit(None)
        assert limit == 0

    @patch("app.services.ai_chat_usage_service.ai_chat_usage")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_error_handling_repository_exception(
        self,
        mock_reset_time,
        mock_current_date,
        mock_repo,
        service: AIChatUsageService,
        mock_user: User,
        mock_dependencies,
    ):
        """Test error handling when repository raises exception."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_repo.get_current_usage_count.side_effect = Exception("Database connection failed")
        mock_dependencies["mock_clerk_service"].get_user_plan.return_value = "standard"

        with pytest.raises(Exception, match="Database connection failed"):
            await service.get_usage_stats(mock_user)
