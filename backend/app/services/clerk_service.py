"""
Clerk API integration service for user plan management with Clerk Billing support.

This service provides methods to retrieve user subscription plans from Clerk API
using the Clerk Billing feature, which integrates with Stripe for subscription management.
The service automatically handles subscription information retrieval and provides
fallback mechanisms for backward compatibility.

Key features:
- Clerk Billing integration for subscription plan retrieval
- Automatic fallback to metadata-based plan information
- Detailed subscription status and renewal information
- Proper error handling and logging
"""

import logging

from clerk_backend_api import Clerk
from clerk_backend_api import User as ClerkUser

logger = logging.getLogger(__name__)


class ClerkService:
    """Clerk APIとの統合サービス"""

    def __init__(self):
        """Initialize Clerk API client"""
        from app.config.auth import ClerkConfig

        clerk_secret_key = ClerkConfig.SECRET_KEY
        if not clerk_secret_key:
            logger.error("CLERK_SECRET_KEY environment variable is not set")
            raise ValueError("CLERK_SECRET_KEY environment variable is required")

        self.client = Clerk(bearer_auth=clerk_secret_key)
        logger.info("ClerkService initialized successfully")

    def get_user_plan(self, user_id: str) -> str:
        """
        ユーザーのサブスクリプションプランを取得（Clerk Billing対応）

        Args:
            user_id: Clerk user ID (string format)

        Returns:
            str: プラン名 ("free", "standard" など)
        """
        try:
            # Clerk APIからユーザー情報を取得
            user: ClerkUser = self.client.users.get(user_id=user_id)

            # Clerk Billingのサブスクリプション情報をチェック
            if hasattr(user, "subscription") and user.subscription:
                subscription = user.subscription

                # サブスクリプションオブジェクトから直接プラン情報を取得
                if hasattr(subscription, "plan") and subscription.plan:
                    plan_name = str(subscription.plan).lower()
                    logger.info(f"Retrieved Clerk Billing plan '{plan_name}' for user {user_id}")
                    return plan_name

                # 辞書形式でアクセスする場合の対応
                if isinstance(subscription, dict) and subscription.get("plan"):
                    plan_name = str(subscription["plan"]).lower()
                    logger.info(f"Retrieved Clerk Billing plan '{plan_name}' (dict access) for user {user_id}")
                    return plan_name

            # フォールバック: メタデータからプラン情報をチェック（既存の実装との互換性）
            if hasattr(user, "public_metadata") and user.public_metadata:
                plan = user.public_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' from public metadata for user {user_id}")
                    return str(plan).lower()

            # プライベートメタデータもチェック
            if hasattr(user, "private_metadata") and user.private_metadata:
                plan = user.private_metadata.get("plan")
                if plan:
                    logger.info(f"Retrieved plan '{plan}' from private metadata for user {user_id}")
                    return str(plan).lower()

            # サブスクリプション情報もメタデータにもプラン情報がない場合はfreeプランにフォールバック
            logger.info(f"No subscription or plan information found for user {user_id}, defaulting to free plan")
            return "free"

        except Exception as e:
            logger.warning(f"Clerk API error for user {user_id}: {e}")
            return "free"  # エラー時はfreeプランにフォールバック

    def get_subscription_info(self, user_id: str) -> dict:
        """
        ユーザーの詳細なサブスクリプション情報を取得（Clerk Billing対応）

        Args:
            user_id: Clerk user ID (string format)

        Returns:
            dict: サブスクリプション情報 {"plan": str, "status": str, "renews_at": str}
        """
        try:
            # Clerk APIからユーザー情報を取得
            user: ClerkUser = self.client.users.get(user_id=user_id)

            # Clerk Billingのサブスクリプション情報をチェック
            if hasattr(user, "subscription") and user.subscription:
                subscription = user.subscription

                # サブスクリプションオブジェクトから情報を取得
                if hasattr(subscription, "plan"):
                    plan_name = str(subscription.plan) if subscription.plan else None
                    status = (
                        str(subscription.status)
                        if hasattr(subscription, "status") and subscription.status
                        else "unknown"
                    )
                    renews_at = (
                        str(subscription.renews_at)
                        if hasattr(subscription, "renews_at") and subscription.renews_at
                        else None
                    )

                    result = {
                        "plan": plan_name.lower() if plan_name else None,
                        "status": status.lower(),
                        "renews_at": renews_at,
                    }
                    logger.info(f"Retrieved subscription info for user {user_id}: {result}")
                    return result

                # 辞書形式でアクセスする場合の対応
                if isinstance(subscription, dict):
                    plan_name = subscription.get("plan")
                    status = subscription.get("status", "unknown")
                    renews_at = subscription.get("renews_at")

                    result = {
                        "plan": str(plan_name).lower() if plan_name else None,
                        "status": str(status).lower(),
                        "renews_at": str(renews_at) if renews_at else None,
                    }
                    logger.info(f"Retrieved subscription info (dict access) for user {user_id}: {result}")
                    return result

            # サブスクリプション情報がない場合
            logger.info(f"No subscription information found for user {user_id}")
            return {"plan": None, "status": "none", "renews_at": None}

        except Exception as e:
            logger.warning(f"Error retrieving subscription info for user {user_id}: {e}")
            return {"plan": None, "status": "error", "renews_at": None}

    def has_subscription(self, user_id: str, plan_name: str) -> bool:
        """
        ユーザーが指定されたプランのサブスクリプションを持っているかチェック

        Args:
            user_id: Clerk user ID (string format)
            plan_name: チェックするプラン名

        Returns:
            bool: 指定されたプランを持っている場合True
        """
        try:
            current_plan = self.get_user_plan(user_id)
            has_plan = current_plan.lower() == plan_name.lower()
            logger.info(f"User {user_id} subscription check: has '{plan_name}' = {has_plan}")
            return has_plan

        except Exception as e:
            logger.warning(f"Error checking subscription for user {user_id}: {e}")
            return False  # エラー時はfalseを返す

    def has_active_subscription(self, user_id: str) -> bool:
        """
        ユーザーがアクティブなサブスクリプションを持っているかチェック

        Args:
            user_id: Clerk user ID (string format)

        Returns:
            bool: アクティブなサブスクリプションを持っている場合True
        """
        try:
            subscription_info = self.get_subscription_info(user_id)
            status = subscription_info.get("status", "none")
            plan = subscription_info.get("plan")

            # アクティブなステータスかつ有効なプランを持っている場合
            is_active = status in ["active", "trialing"] and plan and plan != "free"
            logger.info(f"User {user_id} active subscription check: {is_active} (status: {status}, plan: {plan})")
            return is_active

        except Exception as e:
            logger.warning(f"Error checking active subscription for user {user_id}: {e}")
            return False


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
