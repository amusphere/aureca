"""Tests for AI process endpoint with usage limits integration."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.repositories import ai_chat_usage
from app.schema import User
from app.services.ai_chat_usage_service import AIChatUsageService


class TestAIProcessUsageLimits:
    """Test AI process endpoint with usage limits."""

    async def test_ai_process_with_usage_limit_check(self, session: Session, test_user: User):
        """Test that AI process endpoint checks usage limits before processing."""
        # Create a usage record that's at the limit
        current_date = "2023-01-01"
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 10)

        usage_service = AIChatUsageService(session)

        # Mock the date to match our test data
        with patch.object(usage_service, "_get_current_date", return_value=current_date):
            # Should raise HTTPException when limit is exceeded
            with pytest.raises(HTTPException) as exc_info:
                await usage_service.check_usage_limit(test_user)

            # Verify it's a 429 error (Too Many Requests)
            assert exc_info.value.status_code == 429
            assert "本日の利用回数上限に達しました" in str(exc_info.value.detail)

    async def test_ai_process_increments_usage_after_success(self, session: Session, test_user: User):
        """Test that AI process endpoint increments usage after successful processing."""
        current_date = "2023-01-01"

        usage_service = AIChatUsageService(session)

        # Mock the date to match our test data
        with patch.object(usage_service, "_get_current_date", return_value=current_date):
            # Initially should have 0 usage
            initial_count = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
            assert initial_count == 0

            # Increment usage (simulating successful AI processing)
            await usage_service.increment_usage(test_user)

            # Should now have 1 usage
            final_count = ai_chat_usage.get_current_usage_count(session, test_user.id, current_date)
            assert final_count == 1

    async def test_ai_process_with_free_plan_restriction(self, session: Session, test_user: User):
        """Test that free plan users cannot use AI process."""
        usage_service = AIChatUsageService(session)

        # Mock user plan to be 'free'
        with patch.object(usage_service, "get_user_plan", return_value="free"):
            # Should raise HTTPException for plan restriction
            with pytest.raises(HTTPException) as exc_info:
                await usage_service.check_usage_limit(test_user)

            # Verify it's a 403 error (Forbidden)
            assert exc_info.value.status_code == 403
            assert "現在のプランではAIChatをご利用いただけません" in str(exc_info.value.detail)

    async def test_ai_process_with_available_usage(self, session: Session, test_user: User):
        """Test that AI process works when usage is available."""
        current_date = "2023-01-01"

        usage_service = AIChatUsageService(session)

        # Mock the date to match our test data
        with patch.object(usage_service, "_get_current_date", return_value=current_date):
            # Should work fine when under limit
            result = await usage_service.check_usage_limit(test_user)

            # Should return usage stats
            assert result["can_use_chat"] is True
            assert result["remaining_count"] == 10  # Basic plan limit
            assert result["daily_limit"] == 10

    async def test_usage_stats_calculation(self, session: Session, test_user: User):
        """Test that usage statistics are calculated correctly."""
        current_date = "2023-01-01"

        # Create some usage
        ai_chat_usage.create_daily_usage(session, test_user.id, current_date, 3)

        usage_service = AIChatUsageService(session)

        # Mock the date to match our test data
        with patch.object(usage_service, "_get_current_date", return_value=current_date):
            stats = await usage_service.get_usage_stats(test_user)

            assert stats["current_usage"] == 3
            assert stats["remaining_count"] == 7  # 10 - 3
            assert stats["daily_limit"] == 10
            assert stats["can_use_chat"] is True
