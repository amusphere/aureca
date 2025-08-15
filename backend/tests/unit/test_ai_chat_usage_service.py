"""Unit tests for AI chat usage service functionality using dependency injection."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlmodel import Session

from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import User
from app.services.ai_chat_usage_service import AIChatUsageService
from app.services.clerk_service import ClerkService
from tests.utils.test_data_factory import TestDataFactory
from tests.utils.test_error_scenarios import TestErrorScenarios
from tests.utils.user_factory import UserFactory


class TestAIChatUsageService:
    """Unit tests for AI chat usage service functionality using dependency injection."""

    @pytest.fixture
    def mock_clerk_service(self) -> MagicMock:
        """Create a mock ClerkService for dependency injection."""
        mock_service = MagicMock(spec=ClerkService)
        mock_service.get_user_plan.return_value = "standard"
        return mock_service

    @pytest.fixture
    def mock_usage_repository(self) -> MagicMock:
        """Create a mock AIChatUsageRepository for dependency injection."""
        mock_repo = MagicMock(spec=AIChatUsageRepository)
        mock_repo.get_current_usage_count.return_value = 0
        mock_repo.increment_usage_count.return_value = 1
        mock_repo.get_usage_history.return_value = []
        return mock_repo

    @pytest.fixture
    def service(self, session: Session, mock_clerk_service: MagicMock, mock_usage_repository: MagicMock):
        """Create AIChatUsageService instance with injected dependencies."""
        return AIChatUsageService(
            session=session,
            clerk_service=mock_clerk_service,
            usage_repository=mock_usage_repository,
        )

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing using UserFactory."""
        return UserFactory.build(
            id=1,
            clerk_sub="test_user_123",
            email="test@example.com",
            created_at=1672531200.0,
        )

    def test_get_user_plan_standard(self, service: AIChatUsageService, mock_user: User, mock_clerk_service: MagicMock):
        """Test get_user_plan returns standard plan from Clerk."""
        mock_clerk_service.get_user_plan.return_value = "standard"

        plan = service.get_user_plan(mock_user)
        assert plan == "standard"
        mock_clerk_service.get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    def test_get_user_plan_free(self, service: AIChatUsageService, mock_user: User, mock_clerk_service: MagicMock):
        """Test get_user_plan returns free plan from Clerk."""
        mock_clerk_service.get_user_plan.return_value = "free"

        plan = service.get_user_plan(mock_user)
        assert plan == "free"
        mock_clerk_service.get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    def test_get_daily_limit_free_plan(self, mock_get_limit, service: AIChatUsageService):
        """Test get_daily_limit for free plan."""
        mock_get_limit.return_value = 0

        limit = service.get_daily_limit("free")
        assert limit == 0
        mock_get_limit.assert_called_once_with("free")

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    def test_get_daily_limit_standard_plan(self, mock_get_limit, service: AIChatUsageService):
        """Test get_daily_limit for standard plan."""
        mock_get_limit.return_value = 10

        limit = service.get_daily_limit("standard")
        assert limit == 10
        mock_get_limit.assert_called_once_with("standard")

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    def test_get_daily_limit_unknown_plan(self, mock_get_limit, service: AIChatUsageService):
        """Test get_daily_limit for unknown plan defaults to free."""
        mock_get_limit.return_value = 0

        limit = service.get_daily_limit("unknown_plan")
        assert limit == 0
        mock_get_limit.assert_called_once_with("unknown_plan")

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

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_no_usage(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test get_usage_stats for standard plan user with no usage."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 0

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 10
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 0
        assert stats["reset_time"] == "2023-01-16T00:00:00+00:00"
        assert stats["can_use_chat"] is True
        mock_clerk_service.get_user_plan.assert_called_once_with(mock_user.clerk_sub)
        mock_usage_repository.get_current_usage_count.assert_called_once_with(
            service.session, mock_user.id, "2023-01-15"
        )

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_partial_usage(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test get_usage_stats for standard plan user with partial usage."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 7

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 3
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 7
        assert stats["can_use_chat"] is True

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_limit_reached(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test get_usage_stats for standard plan user who reached limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 10

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 10
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_standard_plan_over_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test get_usage_stats for standard plan user who exceeded limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 15

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0  # Should not go negative
        assert stats["daily_limit"] == 10
        assert stats["current_usage"] == 15
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_get_usage_stats_free_plan_no_access(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test get_usage_stats for free plan user (no access)."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 0
        mock_clerk_service.get_user_plan.return_value = "free"
        mock_usage_repository.get_current_usage_count.return_value = 0

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
    ):
        """Test check_usage_limit raises exception for free plan."""
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
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "get_usage_stats")
    async def test_increment_usage_success(
        self,
        mock_get_stats,
        mock_current_date,
        mock_check_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_usage_repository: MagicMock,
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
        mock_usage_repository.increment_usage_count.assert_called_once_with(service.session, mock_user.id, "2023-01-15")
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
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_increment_usage_database_error(
        self,
        mock_reset_time,
        mock_current_date,
        mock_check_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_usage_repository: MagicMock,
    ):
        """Test increment_usage handles database errors gracefully."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_check_limit.return_value = {"can_use_chat": True}
        mock_usage_repository.increment_usage_count.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await service.increment_usage(mock_user)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "SYSTEM_ERROR" in str(exc_info.value.detail)

    async def test_get_usage_history(
        self, service: AIChatUsageService, mock_user: User, mock_usage_repository: MagicMock
    ):
        """Test get_usage_history returns repository results."""
        mock_logs = [
            TestDataFactory.create_usage_record(user_id=1, usage_date="2023-01-15", usage_count=5, id=1),
            TestDataFactory.create_usage_record(user_id=1, usage_date="2023-01-14", usage_count=3, id=2),
        ]
        mock_usage_repository.get_usage_history.return_value = mock_logs

        result = await service.get_usage_history(mock_user, limit=10)

        mock_usage_repository.get_usage_history.assert_called_once_with(service.session, mock_user.id, 10)
        assert result == mock_logs

    def test_clerk_service_integration(
        self, service: AIChatUsageService, mock_user: User, mock_clerk_service: MagicMock
    ):
        """Test integration with ClerkService for plan retrieval."""
        # Test that the service properly calls ClerkService
        mock_clerk_service.get_user_plan.return_value = "standard"

        plan = service.get_user_plan(mock_user)

        assert plan == "standard"
        mock_clerk_service.get_user_plan.assert_called_once_with(mock_user.clerk_sub)

    def test_clerk_service_error_handling(
        self, service: AIChatUsageService, mock_user: User, mock_clerk_service: MagicMock
    ):
        """Test error handling when ClerkService fails."""
        # Mock ClerkService to raise an exception using TestErrorScenarios
        clerk_error = TestErrorScenarios.simulate_clerk_api_error("Clerk API error")
        mock_clerk_service.get_user_plan.side_effect = clerk_error

        # Should fallback to free plan
        plan = service.get_user_plan(mock_user)

        assert plan == "free"

    # Boundary value tests
    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_exactly_at_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test boundary condition when usage is exactly at limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 10  # Exactly at limit

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0
        assert stats["can_use_chat"] is False

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_one_below_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test boundary condition when usage is one below limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 9  # One below limit

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 1
        assert stats["can_use_chat"] is True

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_boundary_value_one_above_limit(
        self,
        mock_reset_time,
        mock_current_date,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test boundary condition when usage is one above limit."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 11  # One above limit

        stats = await service.get_usage_stats(mock_user)

        assert stats["remaining_count"] == 0  # Should not go negative
        assert stats["can_use_chat"] is False

    # Edge case tests
    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    def test_edge_case_zero_daily_limit(self, mock_get_limit, service: AIChatUsageService):
        """Test edge case with zero daily limit (free plan)."""
        mock_get_limit.return_value = 0

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
        invalid_user = UserFactory.build(id=None, clerk_sub="invalid")
        mock_get_stats.side_effect = Exception("Invalid user")

        with pytest.raises(Exception, match="Invalid user"):
            await service.check_usage_limit(invalid_user)

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    def test_error_handling_invalid_plan_name(self, mock_get_limit, service: AIChatUsageService):
        """Test error handling with invalid plan name."""
        mock_get_limit.return_value = 0

        # Should default to free plan (0 limit)
        limit = service.get_daily_limit("")
        assert limit == 0

        limit = service.get_daily_limit(None)
        assert limit == 0

    @patch.object(AIChatUsageService, "_get_current_date")
    @patch.object(AIChatUsageService, "_get_reset_time")
    async def test_error_handling_repository_exception(
        self,
        mock_reset_time,
        mock_current_date,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test error handling when repository raises exception."""
        mock_current_date.return_value = "2023-01-15"
        mock_reset_time.return_value = "2023-01-16T00:00:00+00:00"
        mock_clerk_service.get_user_plan.return_value = "standard"

        # Use TestErrorScenarios for consistent error simulation
        db_error = TestErrorScenarios.simulate_database_error("Database connection failed")
        mock_usage_repository.get_current_usage_count.side_effect = db_error

        with pytest.raises(Exception, match="Database connection failed"):
            await service.get_usage_stats(mock_user)

    def test_get_user_plan_missing_clerk_sub(self, service: AIChatUsageService, mock_clerk_service: MagicMock):
        """Test get_user_plan with missing clerk_sub."""
        user_without_clerk_sub = User(
            id=1,
            clerk_sub=None,  # Explicitly set to None
            email="test@example.com",
            created_at=1672531200.0,
        )

        plan = service.get_user_plan(user_without_clerk_sub)

        # Should default to standard plan when clerk_sub is missing
        assert plan == "standard"
        # Should not call clerk service when clerk_sub is missing
        mock_clerk_service.get_user_plan.assert_not_called()

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    async def test_can_use_chat_free_plan(
        self, mock_get_limit, service: AIChatUsageService, mock_user: User, mock_clerk_service: MagicMock
    ):
        """Test can_use_chat returns False for free plan."""
        mock_get_limit.return_value = 0
        mock_clerk_service.get_user_plan.return_value = "free"

        result = await service.can_use_chat(mock_user)

        assert result is False

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    async def test_can_use_chat_within_limit(
        self,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test can_use_chat returns True when within limit."""
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 5

        with patch.object(service, "_get_current_date", return_value="2023-01-15"):
            result = await service.can_use_chat(mock_user)

        assert result is True

    @patch("app.services.ai_chat_usage_service.PlanLimits.get_limit")
    async def test_can_use_chat_at_limit(
        self,
        mock_get_limit,
        service: AIChatUsageService,
        mock_user: User,
        mock_clerk_service: MagicMock,
        mock_usage_repository: MagicMock,
    ):
        """Test can_use_chat returns False when at limit."""
        mock_get_limit.return_value = 10
        mock_clerk_service.get_user_plan.return_value = "standard"
        mock_usage_repository.get_current_usage_count.return_value = 10

        with patch.object(service, "_get_current_date", return_value="2023-01-15"):
            result = await service.can_use_chat(mock_user)

        assert result is False
