"""
Integration tests for users API endpoints via HTTP.

Tests the actual HTTP endpoints for users API including the extended /me endpoint
with subscription information.
"""

import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.schema import Subscription, User
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
        """Test GET /api/users/me with no subscription."""
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

    def test_get_current_user_with_active_subscription(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me with active subscription."""
        # Create an active subscription
        future_time = time.time() + 86400 * 30  # 30 days from now
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="active",
            current_period_start=time.time() - 86400,
            current_period_end=future_time,
            cancel_at_period_end=False,
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(subscription)
        session.commit()

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

    def test_get_current_user_with_trial_subscription(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me with trial subscription."""
        # Create a trial subscription
        trial_end = time.time() + 86400 * 7  # 7 days from now
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_trial123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="trialing",
            current_period_start=time.time(),
            current_period_end=trial_end,
            trial_start=time.time(),
            trial_end=trial_end,
            cancel_at_period_end=False,
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(subscription)
        session.commit()

        response = client.get("/api/users/me")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        assert data["subscription"]["isPremium"] is True  # trialing users should have premium access
        assert data["subscription"]["planName"] == "Pro Plan"
        assert data["subscription"]["status"] == "trialing"
        assert data["subscription"]["currentPeriodEnd"] == trial_end

    def test_get_current_user_with_expired_subscription(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me with expired subscription."""
        # Create an expired subscription
        past_time = time.time() - 86400 * 7  # 7 days ago
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_expired123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="active",  # Status is active but period has ended
            current_period_start=time.time() - 86400 * 30,
            current_period_end=past_time,
            cancel_at_period_end=False,
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(subscription)
        session.commit()

        response = client.get("/api/users/me")

        # Verify response - expired subscription should not be considered active
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        # Should not have premium access since subscription is expired
        assert data["subscription"]["isPremium"] is False
        assert data["subscription"]["planName"] is None
        assert data["subscription"]["status"] is None

    def test_get_current_user_with_canceled_subscription(
        self, client: TestClient, session: Session, test_user: User, auth_override
    ):
        """Test GET /api/users/me with canceled subscription."""
        # Create a canceled subscription
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_canceled123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Pro Plan",
            status="canceled",
            current_period_start=time.time() - 86400,
            current_period_end=time.time() + 86400 * 30,  # Future end date but canceled
            cancel_at_period_end=False,
            canceled_at=time.time() - 3600,  # Canceled 1 hour ago
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(subscription)
        session.commit()

        response = client.get("/api/users/me")

        # Verify response - canceled subscription should not be considered active
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_user.id
        # Should not have premium access since subscription is canceled
        assert data["subscription"]["isPremium"] is False
        assert data["subscription"]["planName"] is None
        assert data["subscription"]["status"] is None

    def test_response_model_validation(self, client: TestClient, session: Session, test_user: User, auth_override):
        """Test that the response matches the expected Pydantic model structure."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            plan_name="Premium",
            status="active",
            current_period_start=time.time() - 86400,
            current_period_end=time.time() + 86400 * 30,
            cancel_at_period_end=True,
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(subscription)
        session.commit()

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
