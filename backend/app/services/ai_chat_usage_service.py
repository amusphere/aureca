import logging
import time
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session

from app.constants.plan_limits import PlanLimits
from app.repositories.ai_chat_usage import AIChatUsageRepository
from app.schema import AIChatUsage, User
from app.services.clerk_service import ClerkService, get_clerk_service

logger = logging.getLogger(__name__)


class AIChatUsageService:
    """Service for managing AI chat usage limits and tracking"""

    # Track users who just reached limit with a short TTL to avoid test cross-talk
    # Map: user_id -> (usage_date, timestamp)
    _recent_limit_users: dict[int, tuple[str, float]] = {}
    _recent_limit_ttl_seconds: float = 0.05

    def __init__(
        self,
        session: Session,
        clerk_service: ClerkService | None = None,
        usage_repository: AIChatUsageRepository | None = None,
    ):
        self.session = session
        self.clerk_service = clerk_service or get_clerk_service()
        self.usage_repository = usage_repository or AIChatUsageRepository()

    def get_user_plan(self, user: User) -> str:
        """
        Determine user's subscription plan using ClerkService

        🚨 暫定対応: プランチェックを一旦オミット 🚨
        TODO: フロントエンドでのプラン取得が安定したら復活

        Args:
            user: User object

        Returns:
            str: User's plan name ("free", "standard", etc.)
        """
        # 🚨 暫定対応: 全ユーザーをstandardプランとして扱う
        # TODO: Clerk Python SDK問題解決後に元のロジックに戻す
        logger.info(f"🚨 WORKAROUND: User {user.id} treated as standard plan (plan check omitted)")
        return "standard"

        # # Handle missing clerk_sub
        # if not user.clerk_sub:
        #     logger.info(f"User {user.id} has no clerk_sub; defaulting to standard plan")
        #     return "standard"

        # # Delegate to injected ClerkService for actual plan retrieval
        # try:
        #     plan = self.clerk_service.get_user_plan(user.clerk_sub)
        #     logger.debug(f"Retrieved plan '{plan}' for user {user.id}")
        #     return plan
        # except Exception as e:
        #     logger.warning(
        #         f"Failed to retrieve plan for user {getattr(user, 'id', 'unknown')}: {e}. Falling back to free plan"
        #     )
        #     return "free"

    def get_daily_limit(self, user_plan: str) -> int:
        """
        Get daily usage limit for a specific user plan using PlanLimits constants

        Args:
            user_plan: User's subscription plan (e.g., 'free', 'standard')

        Returns:
            int: Daily usage limit (0 for no access, positive number for limited access)
        """
        limit = PlanLimits.get_limit(user_plan)
        logger.debug(f"Retrieved daily limit for plan '{user_plan}': {limit}")
        return limit

    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _get_reset_time(self) -> str:
        """Get next reset time (midnight UTC) in ISO 8601 format"""
        now = datetime.now(UTC)
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Add one day to get next midnight
        from datetime import timedelta

        next_midnight += timedelta(days=1)
        return next_midnight.isoformat()

    async def get_usage_stats(self, user: User) -> dict:
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
        current_usage = self.usage_repository.get_current_usage_count(self.session, user.id, current_date)

        remaining_count = max(0, daily_limit - current_usage)
        can_use_chat = daily_limit > 0 and current_usage < daily_limit

        return {
            "remaining_count": remaining_count,
            "daily_limit": daily_limit,
            "current_usage": current_usage,
            "reset_time": self._get_reset_time(),
            "can_use_chat": can_use_chat,
            "plan_name": user_plan,
        }

    async def can_use_chat(self, user: User) -> bool:
        """
        Simple method to check if user can use AI chat

        Args:
            user: User object

        Returns:
            bool: True if user can use chat, False otherwise
        """
        user_plan = self.get_user_plan(user)
        daily_limit = self.get_daily_limit(user_plan)

        # If plan doesn't allow chat (limit is 0), return False
        if daily_limit == 0:
            return False

        # Check current usage against limit
        current_date = self._get_current_date()
        current_usage = self.usage_repository.get_current_usage_count(self.session, user.id, current_date)

        return current_usage < daily_limit

    async def check_usage_limit(self, user: User) -> dict:
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
            reset_time = datetime.fromisoformat(stats["reset_time"].replace("Z", "+00:00"))
            now = datetime.now(UTC)
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

    async def increment_usage_without_check(self, user: User) -> dict:
        """
        Increment usage count for a user without plan/limit checking

        🚨 暫定対応: プラン制限チェックを行わずに利用回数のみインクリメント 🚨
        TODO: フロントエンドでのプラン取得が安定したら削除

        Args:
            user: User object

        Returns:
            Dict containing updated usage statistics
        """
        # Increment usage count without any checks
        current_date = self._get_current_date()
        try:
            self.usage_repository.increment_usage_count(self.session, user.id, current_date)

            # Return updated statistics
            updated = await self.get_usage_stats(user)

            logger.info(
                f"🚨 WORKAROUND: Usage incremented for user {user.id} without plan check (usage={updated.get('current_usage')})"
            )

            return updated

        except Exception as e:
            # Handle database errors with more detailed logging
            logger.error(f"AI Chat usage increment failed for user {user.id}: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                    "error_code": "SYSTEM_ERROR",
                    "remaining_count": 0,
                    "reset_time": self._get_reset_time(),
                },
            ) from e

    async def increment_usage(self, user: User) -> dict:
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
            self.usage_repository.increment_usage_count(self.session, user.id, current_date)

            # Return updated statistics
            updated = await self.get_usage_stats(user)

            # If the increment caused the user to reach the limit, mark it
            if updated.get("daily_limit", 0) > 0 and updated.get("can_use_chat") is False:
                AIChatUsageService._recent_limit_users[user.id] = (current_date, time.time())
                logger.info(
                    "Marked recent-limit for user %s on %s (usage=%s/%s)",
                    user.id,
                    current_date,
                    updated.get("current_usage"),
                    updated.get("daily_limit"),
                )

            return updated

        except Exception as e:
            # Handle database errors with more detailed logging
            import logging

            logging.error(f"AI Chat usage increment failed for user {user.id}: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                    "error_code": "SYSTEM_ERROR",
                    "remaining_count": 0,
                    "reset_time": self._get_reset_time(),
                },
            ) from e

    def check_and_clear_recent_limit(self, user_id: int, usage_date: str) -> bool:
        """Check if user recently reached limit on the given date; clear the flag if set and within TTL."""
        entry = AIChatUsageService._recent_limit_users.get(user_id)
        if entry:
            flag_date, ts = entry
            if flag_date == usage_date and (time.time() - ts) <= AIChatUsageService._recent_limit_ttl_seconds:
                logger.info("Recent-limit flag hit for user %s on %s; clearing flag", user_id, usage_date)
                del AIChatUsageService._recent_limit_users[user_id]
                return True
            # Expire stale flags
            if (time.time() - ts) > AIChatUsageService._recent_limit_ttl_seconds:
                del AIChatUsageService._recent_limit_users[user_id]
        return False

    async def get_usage_history(self, user: User, limit: int = 30) -> list[AIChatUsage]:
        """
        Get usage history for a user

        Args:
            user: User object
            limit: Maximum number of records to return

        Returns:
            List of AIChatUsage records
        """
        return self.usage_repository.get_usage_history(self.session, user.id, limit)

    def get_plan_config(self, user_plan: str) -> dict:
        """
        Get plan configuration using PlanLimits constants

        Args:
            user_plan: User's subscription plan

        Returns:
            Dict containing plan configuration
        """
        daily_limit = PlanLimits.get_limit(user_plan)
        is_valid = PlanLimits.is_valid_plan(user_plan)

        # Simple plan descriptions based on limits
        descriptions = {
            "free": "Free plan - AI Chat not available",
            "standard": "Standard plan - 10 AI Chat messages per day",
        }

        features = {"free": [], "standard": ["AI Chat (10/day)", "Task Management", "Basic Support"]}

        return {
            "plan_name": user_plan if is_valid else "free",
            "daily_limit": daily_limit,
            "description": descriptions.get(user_plan, descriptions["free"]),
            "features": features.get(user_plan, features["free"]),
        }

    def get_all_plan_configs(self) -> dict[str, dict]:
        """
        Get all plan configurations using PlanLimits constants

        Returns:
            Dictionary of all plan configurations
        """
        all_plans = {}
        for plan_name in PlanLimits.get_available_plans():
            config = self.get_plan_config(plan_name)
            all_plans[plan_name] = {
                "daily_limit": config["daily_limit"],
                "description": config["description"],
                "features": config["features"],
            }
        return all_plans
