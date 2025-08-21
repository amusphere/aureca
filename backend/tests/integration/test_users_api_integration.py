"""
Integration tests for users API endpoints.

Tests the users API endpoints including the extended /me endpoint
with subscription information.
"""

import pytest
from sqlmodel import Session

from app.models.user import SubscriptionInfo, UserWithSubscriptionModel
from app.schema import Subscription, User
from app.services.user_service import user_service


class TestUsersAPIIntegration:
    """Integration tests for users API endpoints."""

    async def test_get_user_with_subscription_no_subscription(self, session: Session):
        """Test getting user with subscription when user has no subscription."""
        # Create a test user
        user = User(
            id=1,
            clerk_sub="test_user_123",
            email="test@example.com",
            name="Test User",
            created_at=1640995200.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Get user with subscription
        result = await user_service.get_user_with_subscription(user.id, session)

        # Verify the result structure
        assert result["id"] == user.id
        assert result["uuid"] == str(user.uuid)
        assert result["email"] == user.email
        assert result["name"] == user.name
        assert result["subscription"]["isPremium"] is False
        assert result["subscription"]["planName"] is None
        assert result["subscription"]["status"] is None
        assert result["subscription"]["currentPeriodEnd"] is None
        assert result["subscription"]["cancelAtPeriodEnd"] is False

        # Verify the result can be validated by the Pydantic model
        model = UserWithSubscriptionModel(**result)
        assert model.id == user.id
        assert model.subscription.isPremium is False

    async def test_get_user_with_subscription_with_active_subscription(self, session: Session):
        """Test getting user with subscription when user has an active subscription."""
        # Create a test user
        user = User(
            id=1,
            clerk_sub="test_user_123",
            email="test@example.com",
            name="Test User",
            stripe_customer_id="cus_test123",
            created_at=1640995200.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create an active subscription with future end date
        import time

        future_time = time.time() + 86400 * 30  # 30 days from now

        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="active",
            current_period_start=1640995200.0,
            current_period_end=future_time,
            cancel_at_period_end=False,
            created_at=1640995200.0,
            updated_at=1640995200.0,
        )
        session.add(subscription)
        session.commit()

        # Get user with subscription
        result = await user_service.get_user_with_subscription(user.id, session)

        # Verify the result structure
        assert result["id"] == user.id
        assert result["subscription"]["isPremium"] is True
        assert result["subscription"]["planName"] == "Pro Plan"
        assert result["subscription"]["status"] == "active"
        assert result["subscription"]["currentPeriodEnd"] == future_time
        assert result["subscription"]["cancelAtPeriodEnd"] is False
        assert result["subscription"]["stripeSubscriptionId"] == "sub_test123"
        assert result["subscription"]["stripePriceId"] == "price_test123"

        # Verify the result can be validated by the Pydantic model
        model = UserWithSubscriptionModel(**result)
        assert model.subscription.isPremium is True
        assert model.subscription.planName == "Pro Plan"

    async def test_get_user_with_subscription_with_canceled_subscription(self, session: Session):
        """Test getting user with subscription when user has a canceled subscription."""
        # Create a test user
        user = User(
            id=1,
            clerk_sub="test_user_123",
            email="test@example.com",
            name="Test User",
            stripe_customer_id="cus_test123",
            created_at=1640995200.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create a canceled subscription
        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="canceled",
            current_period_start=1640995200.0,
            current_period_end=1672531200.0,
            cancel_at_period_end=True,
            canceled_at=1641081600.0,
            created_at=1640995200.0,
            updated_at=1641081600.0,
        )
        session.add(subscription)
        session.commit()

        # Get user with subscription
        result = await user_service.get_user_with_subscription(user.id, session)

        # Verify the result structure - canceled subscription should not be premium
        # Since get_active_subscription only returns active subscriptions,
        # a canceled subscription should result in no subscription data
        assert result["id"] == user.id
        assert result["subscription"]["isPremium"] is False  # canceled is not premium
        assert result["subscription"]["planName"] is None  # no active subscription
        assert result["subscription"]["status"] is None  # no active subscription
        assert result["subscription"]["cancelAtPeriodEnd"] is False  # default value

    def test_subscription_info_model_validation(self):
        """Test SubscriptionInfo model validation with various data."""
        # Test with premium subscription
        premium_data = {
            "isPremium": True,
            "planName": "Pro Plan",
            "status": "active",
            "currentPeriodEnd": 1672531200.0,
            "cancelAtPeriodEnd": False,
            "stripeSubscriptionId": "sub_123",
            "stripePriceId": "price_123",
        }
        model = SubscriptionInfo(**premium_data)
        assert model.isPremium is True
        assert model.planName == "Pro Plan"

        # Test with free user (no subscription)
        free_data = {
            "isPremium": False,
            "planName": None,
            "status": None,
            "currentPeriodEnd": None,
            "cancelAtPeriodEnd": False,
            "stripeSubscriptionId": None,
            "stripePriceId": None,
        }
        model = SubscriptionInfo(**free_data)
        assert model.isPremium is False
        assert model.planName is None

    async def test_get_user_with_subscription_user_not_found(self, session: Session):
        """Test getting user with subscription when user doesn't exist."""
        with pytest.raises(ValueError, match="User with ID 999 not found"):
            await user_service.get_user_with_subscription(999, session)
