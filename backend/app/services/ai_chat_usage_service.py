from datetime import datetime, timezone
from typing import Dict

from app.database import get_session
from app.repositories import ai_chat_usage
from app.schema import AIChatUsageLog, User
from fastapi import Depends, HTTPException, status
from sqlmodel import Session


class AIChatUsageService:
    """Service for managing AI chat usage limits and tracking"""

    # Plan-based usage limits configuration
    # free: 0 (no access), basic: 10 per day, future plans can be added here
    PLAN_LIMITS: Dict[str, int] = {
        "free": 0,  # No AI chat access for free users
        "basic": 10,  # 10 chats per day for basic plan
        "premium": 50,  # Future expansion
        "enterprise": -1,  # Unlimited (future expansion)
    }

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_user_plan(self, user: User) -> str:
        """
        Determine user's subscription plan

        Args:
            user: User object

        Returns:
            str: User's plan name

        Note: Currently defaults to 'basic' for all authenticated users.
        This should be extended when subscription system is implemented.
        """
        # TODO: Implement actual subscription plan detection
        # For now, all authenticated users get 'basic' plan
        # Free users would not be authenticated or have a specific flag
        return "basic"

    def get_daily_limit(self, user_plan: str) -> int:
        """
        Get daily usage limit for a specific user plan

        Args:
            user_plan: User's subscription plan (e.g., 'free', 'basic')

        Returns:
            int: Daily usage limit (-1 for unlimited, 0 for no access)
        """
        return self.PLAN_LIMITS.get(user_plan, 0)  # Default to free plan (no access)

    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _get_reset_time(self) -> str:
        """Get next reset time (midnight UTC) in ISO 8601 format"""
        now = datetime.now(timezone.utc)
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Add one day to get next midnight
        from datetime import timedelta

        next_midnight += timedelta(days=1)
        return next_midnight.isoformat()

    async def get_usage_stats(self, user: User) -> Dict:
        """
        Get current usage statistics for a user

        Args:
            user: User object

        Returns:
            Dict containing usage statistics
        """
        user_plan = self.get_user_plan(user)
        current_date = self._get_current_date()
        daily_limit = self.get_daily_limit(user_plan)
        current_usage = ai_chat_usage.get_current_usage_count(
            self.session, user.id, current_date
        )

        remaining_count = (
            max(0, daily_limit - current_usage) if daily_limit >= 0 else -1
        )
        can_use_chat = daily_limit == -1 or (
            daily_limit > 0 and current_usage < daily_limit
        )

        return {
            "remaining_count": remaining_count,
            "daily_limit": daily_limit,
            "current_usage": current_usage,
            "reset_time": self._get_reset_time(),
            "can_use_chat": can_use_chat,
        }

    async def check_usage_limit(self, user: User) -> Dict:
        """
        Check if user can use AI chat based on their plan and current usage

        Args:
            user: User object

        Returns:
            Dict containing usage check result

        Raises:
            HTTPException: If usage limit is exceeded or plan doesn't allow access
        """
        stats = await self.get_usage_stats(user)

        # Check if plan allows AI chat access
        if stats["daily_limit"] == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "現在のプランではAIChatをご利用いただけません。プランをアップグレードしてください。",
                    "error_code": "PLAN_RESTRICTION",
                    "remaining_count": 0,
                    "reset_time": stats["reset_time"],
                },
            )

        # Check if daily limit is exceeded (for non-unlimited plans)
        if stats["daily_limit"] > 0 and not stats["can_use_chat"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "本日の利用回数上限に達しました。明日の00:00にリセットされます。",
                    "error_code": "USAGE_LIMIT_EXCEEDED",
                    "remaining_count": stats["remaining_count"],
                    "reset_time": stats["reset_time"],
                },
            )

        return {
            "remaining_count": stats["remaining_count"],
            "daily_limit": stats["daily_limit"],
            "reset_time": stats["reset_time"],
            "can_use_chat": stats["can_use_chat"],
        }

    async def increment_usage(self, user: User) -> Dict:
        """
        Increment usage count for a user after successful AI chat usage

        Args:
            user: User object

        Returns:
            Dict containing updated usage statistics

        Raises:
            HTTPException: If usage limit would be exceeded
        """
        # First check if user can use AI chat
        await self.check_usage_limit(user)

        # Increment usage count
        current_date = self._get_current_date()
        try:
            ai_chat_usage.increment_daily_usage(self.session, user.id, current_date)

            # Return updated statistics
            return await self.get_usage_stats(user)

        except Exception:
            # Handle database errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                    "error_code": "SYSTEM_ERROR",
                    "remaining_count": 0,
                    "reset_time": self._get_reset_time(),
                },
            )

    async def get_usage_history(
        self, user: User, limit: int = 30
    ) -> list[AIChatUsageLog]:
        """
        Get usage history for a user

        Args:
            user: User object
            limit: Maximum number of records to return

        Returns:
            List of AIChatUsageLog records
        """
        return ai_chat_usage.get_usage_history(self.session, user.id, limit)

    def update_plan_limits(self, new_limits: Dict[str, int]) -> None:
        """
        Update plan limits configuration (for future admin functionality)

        Args:
            new_limits: Dictionary of plan names to daily limits
        """
        self.PLAN_LIMITS.update(new_limits)

    def get_all_plan_limits(self) -> Dict[str, int]:
        """
        Get all configured plan limits

        Returns:
            Dictionary of all plan limits
        """
        return self.PLAN_LIMITS.copy()
