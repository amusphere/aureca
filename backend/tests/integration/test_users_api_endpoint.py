"""
Integration tests for users API endpoints via HTTP.

Tests the actual HTTP endpoints for users API including the extended /me endpoint
with subscription information fetched from Stripe API.
"""

import time
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.schema import User
from app.services.auth import auth_user
from main import app


@pytest.fixture(name="auth_override")
def auth_override_fixture(test_user: User) -> Generator[None, None, None]:
    """Override auth_user dependency for testing."""
    app.dependency_overrides[auth_user] = lambda: test_user
    yield
    if auth_user in app.dependency_overrides:
        del app.dependency_overrides[auth_user]


class TestUsersAPIEndpoint:
    """Integration tests for users API HTTP endpoints."""

    def test_get_current_user_no_subscription(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me with no subscription (no Stripe customer)."""
        # Ensure user has no Stripe customer ID
        test_user.stripe_customer_id = None
        session.add(test_user)
        session.commit()

        response = client.get("/api/users/me")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["uuid"] == str(test_user.uuid)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["subscription"]["isPremium"] is False
        assert data["subscription"]["planName"] is None
        assert data["subscription"]["status"] is None
        assert data["subscription"]["currentPeriodEnd"] is None
        assert data["subscription"]["cancelAtPeriodEnd"] is False

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_subscription_premium")
    @patch("app.services.stripe_service.StripeService.get_subscription_plan_name")
    @patch("app.services.stripe_service.StripeService.is_configured")
    def test_get_current_user_with_active_subscription(
        self,
        mock_is_configured,
        mock_get_plan_name,
        mock_is_premium,
        mock_get_subscription,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_override,
    ):
        """Test GET /api/users/me with active subscription from Stripe."""
        # Set up user with Stripe customer ID
        test_user.stripe_customer_id = "cus_test123"
        session.add(test_user)
        session.commit()

        # Mock Stripe service responses
        mock_is_configured.return_value = True

        # Create mock subscription object
        future_time = int(time.time() + 86400 * 30)  # 30 days from now
        mock_subscription = Mock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = future_time
        mock_subscription.cancel_at_period_end = False
        mock_subscription.items.data = [Mock()]
        mock_subscription.items.data[0].price.id = "price_test123"

        mock_get_subscription.return_value = mock_subscription
        mock_is_premium.return_value = True
        mock_get_plan_name.return_value = "Pro Plan"

        response = client.get("/api/users/me")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["subscription"]["isPremium"] is True
        assert data["subscription"]["planName"] == "Pro Plan"
        assert data["subscription"]["status"] == "active"
        assert data["subscription"]["currentPeriodEnd"] == future_time
        assert data["subscription"]["cancelAtPeriodEnd"] is False
        assert data["subscription"]["stripeSubscriptionId"] == "sub_test123"
        assert data["subscription"]["stripePriceId"] == "price_test123"

    def test_get_current_user_basic_endpoint(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me/basic endpoint for backward compatibility."""
        response = client.get("/api/users/me/basic")

        # Verify response - should only contain basic user info
        assert response.status_code == 200
        data = response.json()

        assert data["uuid"] == str(test_user.uuid)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        # Should not contain subscription information
        assert "subscription" not in data
        assert "id" not in data  # Basic model doesn't include id

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test GET /api/users/me without authentication."""
        # Don't use auth_override fixture, so it should fail authentication
        response = client.get("/api/users/me")

        # Should return 401 or 403 depending on auth implementation
        assert response.status_code in [401, 403]

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_subscription_premium")
    @patch("app.services.stripe_service.StripeService.get_subscription_plan_name")
    @patch("app.services.stripe_service.StripeService.is_configured")
    def test_get_current_user_with_trial_subscription(
        self,
        mock_is_configured,
        mock_get_plan_name,
        mock_is_premium,
        mock_get_subscription,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_override,
    ):
        """Test GET /api/users/me with trial subscription from Stripe."""
        # Set up user with Stripe customer ID
        test_user.stripe_customer_id = "cus_test123"
        session.add(test_user)
        session.commit()

        # Mock Stripe service responses
        mock_is_configured.return_value = True

        # Create mock trial subscription object
        trial_end = int(time.time() + 86400 * 7)  # 7 days from now
        mock_subscription = Mock()
        mock_subscription.id = "sub_trial123"
        mock_subscription.status = "trialing"
        mock_subscription.current_period_end = trial_end
        mock_subscription.cancel_at_period_end = False
        mock_subscription.items.data = [Mock()]
        mock_subscription.items.data[0].price.id = "price_test123"

        mock_get_subscription.return_value = mock_subscription
        mock_is_premium.return_value = True  # trialing users should have premium access
        mock_get_plan_name.return_value = "Pro Plan"

        response = client.get("/api/users/me")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["subscription"]["isPremium"] is True  # trialing users should have premium access
        assert data["subscription"]["planName"] == "Pro Plan"
        assert data["subscription"]["status"] == "trialing"
        assert data["subscription"]["currentPeriodEnd"] == trial_end

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_configured")
    def test_get_current_user_with_expired_subscription(
        self,
        mock_is_configured,
        mock_get_subscription,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_override,
    ):
        """Test GET /api/users/me with no active subscription (expired handled by Stripe)."""
        # Set up user with Stripe customer ID
        test_user.stripe_customer_id = "cus_test123"
        session.add(test_user)
        session.commit()

        # Mock Stripe service responses - no active subscription returned
        mock_is_configured.return_value = True
        mock_get_subscription.return_value = None  # No active subscription

        response = client.get("/api/users/me")

        # Verify response - no active subscription should not provide premium access
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        # Should not have premium access since no active subscription
        assert data["subscription"]["isPremium"] is False
        assert data["subscription"]["planName"] is None
        assert data["subscription"]["status"] is None

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_configured")
    def test_get_current_user_with_canceled_subscription(
        self,
        mock_is_configured,
        mock_get_subscription,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_override,
    ):
        """Test GET /api/users/me with canceled subscription (handled by Stripe)."""
        # Set up user with Stripe customer ID
        test_user.stripe_customer_id = "cus_test123"
        session.add(test_user)
        session.commit()

        # Mock Stripe service responses - no active subscription returned (canceled subscriptions are not active)
        mock_is_configured.return_value = True
        mock_get_subscription.return_value = None  # Canceled subscriptions are not returned as active

        response = client.get("/api/users/me")

        # Verify response - canceled subscription should not be considered active
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        # Should not have premium access since subscription is canceled
        assert data["subscription"]["isPremium"] is False
        assert data["subscription"]["planName"] is None
        assert data["subscription"]["status"] is None

    @patch("app.services.stripe_service.StripeService.get_active_subscription")
    @patch("app.services.stripe_service.StripeService.is_subscription_premium")
    @patch("app.services.stripe_service.StripeService.get_subscription_plan_name")
    @patch("app.services.stripe_service.StripeService.is_configured")
    def test_response_model_validation(
        self,
        mock_is_configured,
        mock_get_plan_name,
        mock_is_premium,
        mock_get_subscription,
        client: TestClient,
        session: Session,
        test_user: User,
        auth_override,
    ):
        """Test that the response matches the expected Pydantic model structure."""
        # Set up user with Stripe customer ID
        test_user.stripe_customer_id = "cus_test123"
        session.add(test_user)
        session.commit()

        # Mock Stripe service responses
        mock_is_configured.return_value = True

        # Create mock subscription object
        future_time = int(time.time() + 86400 * 30)  # 30 days from now
        mock_subscription = Mock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = future_time
        mock_subscription.cancel_at_period_end = True
        mock_subscription.items.data = [Mock()]
        mock_subscription.items.data[0].price.id = "price_test123"

        mock_get_subscription.return_value = mock_subscription
        mock_is_premium.return_value = True
        mock_get_plan_name.return_value = "Premium"

        response = client.get("/api/users/me")

        # Verify response structure matches UserWithSubscriptionModel
        assert response.status_code == 200
        data = response.json()

        # Required fields from UserWithSubscriptionModel
        required_fields = [
            "id",
            "uuid",
            "email",
            "name",
            "clerk_sub",
            "stripe_customer_id",
            "created_at",
            "subscription",
        ]
        for field in required_fields:
            assert field in data

        # Required subscription fields from SubscriptionInfo
        subscription_fields = [
            "isPremium",
            "planName",
            "status",
            "currentPeriodEnd",
            "cancelAtPeriodEnd",
            "stripeSubscriptionId",
            "stripePriceId",
        ]
        for field in subscription_fields:
            assert field in data["subscription"]

        # Verify data types
        assert isinstance(data["id"], int)
        assert isinstance(data["uuid"], str)
        assert isinstance(data["created_at"], float)
        assert isinstance(data["subscription"]["isPremium"], bool)
        assert isinstance(data["subscription"]["cancelAtPeriodEnd"], bool)
