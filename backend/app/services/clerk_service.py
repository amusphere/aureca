"""
Clerk API integration service for user plan management.

This service provides methods to retrieve user subscription plans from Clerk API
with proper error handling and fallback mechanisms.
"""

import logging
import os

from clerk_backend_api import Clerk
from clerk_backend_api import User as ClerkUser

logger = logging.getLogger(__name__)


class ClerkService:
    """Clerk APIとの統合サービス"""

    def __init__(self):
        """Initialize Clerk API client"""
        clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        if not clerk_secret_key:
            logger.error("CLERK_SECRET_KEY environment variable is not set")
            raise ValueError("CLERK_SECRET_KEY environment variable is required")

        self.client = Clerk(bearer_auth=clerk_secret_key)
        logger.info("ClerkService initialized successfully")

    async def get_user_plan(self, user_id: str) -> str:
        """
        ユーザーのサブスクリプションプランを取得

        Args:
            user_id: Clerk user ID (string format)

        Returns:
            str: プラン名 ("free", "standard" など)
        """
        try:
            # Clerk APIからユーザー情報を取得
            user: ClerkUser = self.client.users.get(user_id=user_id)

            # サブスクリプション情報をチェック
            if hasattr(user, "public_metadata") and user.public_metadata:
                plan = user.public_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' for user {user_id}")
                    return str(plan).lower()

            # プライベートメタデータもチェック
            if hasattr(user, "private_metadata") and user.private_metadata:
                plan = user.private_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' from private metadata for user {user_id}")
                    return str(plan).lower()

            # メタデータにプラン情報がない場合はfreeプランにフォールバック
            logger.info(f"No plan information found for user {user_id}, defaulting to free plan")
            return "free"

        except Exception as e:
            logger.warning(f"Clerk API error for user {user_id}: {e}")
            return "free"  # エラー時はfreeプランにフォールバック

    async def has_subscription(self, user_id: str, plan_name: str) -> bool:
        """
        ユーザーが指定されたプランのサブスクリプションを持っているかチェック

        Args:
            user_id: Clerk user ID (string format)
            plan_name: チェックするプラン名

        Returns:
            bool: 指定されたプランを持っている場合True
        """
        try:
            current_plan = await self.get_user_plan(user_id)
            has_plan = current_plan.lower() == plan_name.lower()
            logger.info(f"User {user_id} subscription check: has '{plan_name}' = {has_plan}")
            return has_plan

        except Exception as e:
            logger.warning(f"Error checking subscription for user {user_id}: {e}")
            return False  # エラー時はfalseを返す

    def get_user_plan_sync(self, user_id: str) -> str:
        """
        ユーザーのサブスクリプションプランを同期的に取得

        Args:
            user_id: Clerk user ID (string format)

        Returns:
            str: プラン名 ("free", "standard" など)
        """
        try:
            # Clerk APIからユーザー情報を取得
            user: ClerkUser = self.client.users.get(user_id=user_id)

            # サブスクリプション情報をチェック
            if hasattr(user, "public_metadata") and user.public_metadata:
                plan = user.public_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' for user {user_id}")
                    return str(plan).lower()

            # プライベートメタデータもチェック
            if hasattr(user, "private_metadata") and user.private_metadata:
                plan = user.private_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' from private metadata for user {user_id}")
                    return str(plan).lower()

            # メタデータにプラン情報がない場合はfreeプランにフォールバック
            logger.info(f"No plan information found for user {user_id}, defaulting to free plan")
            return "free"

        except Exception as e:
            logger.warning(f"Clerk API error for user {user_id}: {e}")
            return "free"  # エラー時はfreeプランにフォールバック


# Global service instance
_clerk_service: ClerkService | None = None


def get_clerk_service() -> ClerkService:
    """
    Get global ClerkService instance (singleton pattern)

    Returns:
        ClerkService: Global service instance
    """
    global _clerk_service
    if _clerk_service is None:
        _clerk_service = ClerkService()
    return _clerk_service
