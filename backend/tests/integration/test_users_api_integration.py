"""
Integration tests for users API endpoints.

Tests the users API endpoints including the extended /me endpoint
with subscription information from Stripe API.
"""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from app.models.user import SubscriptionInfo, UserWithSubscriptionModel
from app.schema import User
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

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_subscription_premium")
    @patch("app.services.stripe_service.StripeService.get_subscription_plan_name")
    @patch("app.services.stripe_service.StripeService.is_configured")
    async def test_get_user_with_subscription_with_active_subscription(
        self, mock_is_configured, mock_get_plan_name, mock_is_premium, mock_get_subscription, session: Session
    ):
        """Test getting user with subscription when user has an active subscription from Stripe."""
        # Create a test user with Stripe customer ID
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

        # Mock Stripe service responses
        import time

        future_time = int(time.time() + 86400 * 30)  # 30 days from now

        mock_is_configured.return_value = True

        # Create mock Stripe subscription
        mock_stripe_subscription = Mock()
        mock_stripe_subscription.id = "sub_test123"
        mock_stripe_subscription.status = "active"
        mock_stripe_subscription.current_period_end = future_time
        mock_stripe_subscription.cancel_at_period_end = False
        mock_stripe_subscription.items.data = [Mock()]
        mock_stripe_subscription.items.data[0].price.id = "price_test123"

        mock_get_subscription.return_value = mock_stripe_subscription
        mock_is_premium.return_value = True
        mock_get_plan_name.return_value = "Pro Plan"

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

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_configured")
    async def test_get_user_with_subscription_with_canceled_subscription(
        self, mock_is_configured, mock_get_subscription, session: Session
    ):
        """Test getting user with subscription when user has a canceled subscription (handled by Stripe)."""
        # Create a test user with Stripe customer ID
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

        # Mock Stripe service responses - canceled subscriptions are not returned as active
        mock_is_configured.return_value = True
        mock_get_subscription.return_value = None  # Canceled subscriptions are not active

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
