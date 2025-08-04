from datetime import datetime, timezone
from typing import Dict

from app.config import get_ai_chat_plan_limit, get_ai_chat_plan_config, get_all_ai_chat_plans
from app.database import get_session
from app.repositories import ai_chat_usage
from app.schema import AIChatUsageLog, User
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
import logging

logger = logging.getLogger(__name__)


class AIChatUsageService:
    """Service for managing AI chat usage limits and tracking"""

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
        limit = get_ai_chat_plan_limit(user_plan)
        logger.debug(f"Retrieved daily limit for plan '{user_plan}': {limit}")
        return limit

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

        # Get plan configuration for additional context
        plan_config = self.get_plan_config(user_plan)

        return {
            "remaining_count": remaining_count,
            "daily_limit": daily_limit,
            "current_usage": current_usage,
            "reset_time": self._get_reset_time(),
            "can_use_chat": can_use_chat,
            "plan_name": user_plan,
            "plan_description": plan_config.get("description", ""),
            "plan_features": plan_config.get("features", []),
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
                    "error": "現在のプランではAIChatをご利用いただけません。プランをアップグレードしてご利用ください。",
                    "error_code": "PLAN_RESTRICTION",
                    "remaining_count": 0,
                    "reset_time": stats["reset_time"],
                },
            )

        # Check if daily limit is exceeded (for non-unlimited plans)
        if stats["daily_limit"] > 0 and not stats["can_use_chat"]:
            # Calculate time until reset for better user experience
            reset_time = datetime.fromisoformat(
                stats["reset_time"].replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            time_diff = reset_time - now
            hours_until_reset = max(0, int(time_diff.total_seconds() / 3600))

            reset_message = "本日の利用回数上限に達しました。"
            if hours_until_reset > 0:
                reset_message += f"約{hours_until_reset}時間後にリセットされます。"
            else:
                reset_message += "まもなくリセットされます。"

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": reset_message,
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

        except Exception as e:
            # Handle database errors with more detailed logging
            import logging

            logging.error(
                f"AI Chat usage increment failed for user {user.id}: {str(e)}"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。",
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

    def get_plan_config(self, user_plan: str) -> Dict:
        """
        Get full plan configuration including features and description

        Args:
            user_plan: User's subscription plan

        Returns:
            Dict containing plan configuration
        """
        plan_config = get_ai_chat_plan_config(user_plan)
        if plan_config:
            return {
                "plan_name": user_plan,
                "daily_limit": plan_config.daily_limit,
                "description": plan_config.description,
                "features": plan_config.features
            }

        # Return default free plan config if plan not found
        logger.warning(f"Plan '{user_plan}' not found, returning free plan config")
        free_config = get_ai_chat_plan_config("free")
        return {
            "plan_name": "free",
            "daily_limit": free_config.daily_limit if free_config else 0,
            "description": free_config.description if free_config else "Free plan",
            "features": free_config.features if free_config else []
        }

    def update_plan_limits(self, new_limits: Dict[str, int]) -> None:
        """
        Update plan limits configuration (for backward compatibility)

        This method is deprecated. Use the configuration management system instead.

        Args:
            new_limits: Dictionary of plan names to daily limits
        """
        from app.config import update_ai_chat_plan_limit

        for plan_name, daily_limit in new_limits.items():
            update_ai_chat_plan_limit(plan_name, daily_limit)

        logger.warning("update_plan_limits is deprecated. Use configuration management system instead.")

    def get_all_plan_limits(self) -> Dict[str, int]:
        """
        Get all configured plan limits

        Returns:
            Dictionary of all plan limits
        """
        all_plans = get_all_ai_chat_plans()
        return {plan_name: plan_config.daily_limit for plan_name, plan_config in all_plans.items()}

    def get_all_plan_configs(self) -> Dict[str, Dict]:
        """
        Get all plan configurations with full details

        Returns:
            Dictionary of all plan configurations
        """
        all_plans = get_all_ai_chat_plans()
        return {
            plan_name: {
                "daily_limit": plan_config.daily_limit,
                "description": plan_config.description,
                "features": plan_config.features
            }
            for plan_name, plan_config in all_plans.items()
        }
