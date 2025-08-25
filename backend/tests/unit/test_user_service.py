"""
Unit tests for UserService.

Tests the UserService functionality including Stripe customer management
and user data retrieval with subscription information from Stripe API.
"""

import time
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.schema import User
from app.services.stripe_service import StripeService
from app.services.user_service import UserService


class TestUserService:
    """Test cases for UserService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_stripe_service = Mock(spec=StripeService)
        self.mock_stripe_service.is_configured = Mock(return_value=True)
        self.mock_stripe_service.create_customer = AsyncMock()
        self.mock_stripe_service.get_active_subscription = AsyncMock()
        self.mock_stripe_service.is_subscription_premium = Mock()
        self.mock_stripe_service.get_subscription_plan_name = Mock()

        self.user_service = UserService(stripe_service=self.mock_stripe_service)

        # Create a mock user
        self.mock_user = User(
            id=1,
            uuid=uuid4(),
            email="test@example.com",
            name="Test User",
            clerk_sub="test_clerk_sub",
            created_at=time.time(),
        )

        # Create a mock session
        self.mock_session = Mock(spec=Session)

    @pytest.mark.asyncio
    async def test_ensure_stripe_customer_existing_customer(self):
        """Test ensure_stripe_customer when user already has stripe_customer_id."""
        # Arrange
        self.mock_user.stripe_customer_id = "cus_existing123"

        # Act
        result = await self.user_service.ensure_stripe_customer(self.mock_user, self.mock_session)

        # Assert
        assert result == "cus_existing123"
        self.mock_stripe_service.create_customer.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_stripe_customer_create_new(self):
        """Test ensure_stripe_customer when creating a new Stripe customer."""
        # Arrange
        self.mock_user.stripe_customer_id = None
        self.mock_stripe_service.is_configured.return_value = True
        self.mock_stripe_service.create_customer.return_value = "cus_new123"

        with patch("app.repositories.user.update_user_stripe_customer_id") as mock_update:
            mock_update.return_value = self.mock_user

            # Act
            result = await self.user_service.ensure_stripe_customer(self.mock_user, self.mock_session)

            # Assert
            assert result == "cus_new123"
            self.mock_stripe_service.create_customer.assert_called_once_with(self.mock_user)
            mock_update.assert_called_once_with(self.mock_session, self.mock_user.id, "cus_new123")

    @pytest.mark.asyncio
    async def test_ensure_stripe_customer_not_configured(self):
        """Test ensure_stripe_customer when Stripe is not configured."""
        # Arrange
        self.mock_stripe_service.is_configured.return_value = False

        # Act & Assert
        with pytest.raises(ValueError, match="Stripe is not configured"):
            await self.user_service.ensure_stripe_customer(self.mock_user, self.mock_session)

    @pytest.mark.asyncio
    async def test_ensure_stripe_customer_stripe_error(self):
        """Test ensure_stripe_customer when Stripe API fails."""
        # Arrange
        from stripe.error import StripeError

        self.mock_user.stripe_customer_id = None
        self.mock_stripe_service.is_configured.return_value = True
        self.mock_stripe_service.create_customer.side_effect = StripeError("API Error")

        # Act & Assert
        with pytest.raises(StripeError):
            await self.user_service.ensure_stripe_customer(self.mock_user, self.mock_session)

    @pytest.mark.asyncio
    async def test_get_user_with_subscription_with_active_subscription(self):
        """Test get_user_with_subscription with an active subscription from Stripe."""
        # Arrange
        self.mock_user.stripe_customer_id = "cus_123"

        # Create mock Stripe subscription
        mock_stripe_subscription = Mock()
        mock_stripe_subscription.id = "sub_123"
        mock_stripe_subscription.status = "active"
        mock_stripe_subscription.current_period_end = int(time.time() + 86400)
        mock_stripe_subscription.cancel_at_period_end = False
        mock_stripe_subscription.items.data = [Mock()]
        mock_stripe_subscription.items.data[0].price.id = "price_123"

        self.mock_stripe_service.get_active_subscription.return_value = mock_stripe_subscription
        self.mock_stripe_service.is_subscription_premium.return_value = True
        self.mock_stripe_service.get_subscription_plan_name.return_value = "Premium"

        with patch("app.repositories.user.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = self.mock_user

            # Act
            result = await self.user_service.get_user_with_subscription(1, self.mock_session)

            # Assert
            assert result["id"] == 1
            assert result["email"] == "test@example.com"
            assert result["subscription"]["isPremium"] is True
            assert result["subscription"]["planName"] == "Premium"
            assert result["subscription"]["status"] == "active"
            assert result["subscription"]["stripeSubscriptionId"] == "sub_123"
            assert result["subscription"]["stripePriceId"] == "price_123"

    @pytest.mark.asyncio
    async def test_get_user_with_subscription_no_subscription(self):
        """Test get_user_with_subscription with no active subscription."""
        # Arrange
        self.mock_user.stripe_customer_id = "cus_123"
        self.mock_stripe_service.get_active_subscription.return_value = None

        with patch("app.repositories.user.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = self.mock_user

            # Act
            result = await self.user_service.get_user_with_subscription(1, self.mock_session)

            # Assert
            assert result["id"] == 1
            assert result["email"] == "test@example.com"
            assert result["subscription"]["isPremium"] is False
            assert result["subscription"]["planName"] is None
            assert result["subscription"]["status"] is None

    @pytest.mark.asyncio
    async def test_get_user_with_subscription_user_not_found(self):
        """Test get_user_with_subscription when user doesn't exist."""
        # Arrange
        with patch("app.repositories.user.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = None

            # Act & Assert
            with pytest.raises(ValueError, match="User with ID 999 not found"):
                await self.user_service.get_user_with_subscription(999, self.mock_session)

    @pytest.mark.asyncio
    async def test_update_user_stripe_customer_id_success(self):
        """Test update_user_stripe_customer_id success case."""
        # Arrange
        with patch("app.repositories.user.update_user_stripe_customer_id") as mock_update:
            mock_update.return_value = self.mock_user

            # Act
            result = await self.user_service.update_user_stripe_customer_id(1, "cus_new123", self.mock_session)

            # Assert
            assert result == self.mock_user
            mock_update.assert_called_once_with(self.mock_session, 1, "cus_new123")

    @pytest.mark.asyncio
    async def test_get_user_with_subscription_with_trialing_subscription(self):
        """Test get_user_with_subscription with a trialing subscription from Stripe."""
        # Arrange
        self.mock_user.stripe_customer_id = "cus_123"

        # Create mock Stripe trial subscription
        mock_stripe_subscription = Mock()
        mock_stripe_subscription.id = "sub_trial123"
        mock_stripe_subscription.status = "trialing"
        mock_stripe_subscription.current_period_end = int(time.time() + 86400 * 7)
        mock_stripe_subscription.cancel_at_period_end = False
        mock_stripe_subscription.items.data = [Mock()]
        mock_stripe_subscription.items.data[0].price.id = "price_123"

        self.mock_stripe_service.get_active_subscription.return_value = mock_stripe_subscription
        self.mock_stripe_service.is_subscription_premium.return_value = (
            True  # Trialing users should have premium access
        )
        self.mock_stripe_service.get_subscription_plan_name.return_value = "Premium"

        with patch("app.repositories.user.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = self.mock_user

            # Act
            result = await self.user_service.get_user_with_subscription(1, self.mock_session)

            # Assert
            assert result["id"] == 1
            assert result["email"] == "test@example.com"
            assert result["subscription"]["isPremium"] is True  # Trialing users should have premium access
            assert result["subscription"]["planName"] == "Premium"
            assert result["subscription"]["status"] == "trialing"

    @pytest.mark.asyncio
    async def test_update_user_stripe_customer_id_user_not_found(self):
        """Test update_user_stripe_customer_id when user doesn't exist."""
        # Arrange
        with patch("app.repositories.user.update_user_stripe_customer_id") as mock_update:
            mock_update.return_value = None

            # Act & Assert
            with pytest.raises(ValueError, match="User with ID 999 not found"):
                await self.user_service.update_user_stripe_customer_id(999, "cus_new123", self.mock_session)

    @pytest.mark.asyncio
    async def test_get_user_with_subscription_no_stripe_customer(self):
        """Test get_user_with_subscription when user has no Stripe customer ID."""
        # Arrange
        self.mock_user.stripe_customer_id = None

        with patch("app.repositories.user.get_user_by_id") as mock_get_user:
            mock_get_user.return_value = self.mock_user

            # Act
            result = await self.user_service.get_user_with_subscription(1, self.mock_session)

            # Assert
            assert result["id"] == 1
            assert result["email"] == "test@example.com"
            assert result["subscription"]["isPremium"] is False
            assert result["subscription"]["planName"] is None
            assert result["subscription"]["status"] is None
            # Should not call Stripe API when no customer ID
            self.mock_stripe_service.get_active_subscription.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_subscription_info_with_active_subscription(self):
        """Test get_subscription_info method with active subscription."""
        # Arrange
        self.mock_user.stripe_customer_id = "cus_123"

        # Create mock Stripe subscription
        mock_stripe_subscription = Mock()
        mock_stripe_subscription.id = "sub_123"
        mock_stripe_subscription.status = "active"
        mock_stripe_subscription.current_period_end = int(time.time() + 86400)
        mock_stripe_subscription.cancel_at_period_end = False
        mock_stripe_subscription.items.data = [Mock()]
        mock_stripe_subscription.items.data[0].price.id = "price_123"

        self.mock_stripe_service.get_active_subscription.return_value = mock_stripe_subscription
        self.mock_stripe_service.is_subscription_premium.return_value = True
        self.mock_stripe_service.get_subscription_plan_name.return_value = "Premium"

        # Act
        result = await self.user_service.get_subscription_info(self.mock_user)

        # Assert
        assert result["isPremium"] is True
        assert result["planName"] == "Premium"
        assert result["status"] == "active"
        assert result["stripeSubscriptionId"] == "sub_123"
        assert result["stripePriceId"] == "price_123"

    @pytest.mark.asyncio
    async def test_ensure_user_has_stripe_customer_success(self):
        """Test ensure_user_has_stripe_customer method."""
        # Arrange
        self.mock_user.stripe_customer_id = None
        self.mock_stripe_service.create_customer.return_value = "cus_new123"

        with (
            patch("app.repositories.user.get_user_by_id") as mock_get_user,
            patch("app.repositories.user.update_user_stripe_customer_id") as mock_update,
        ):
            mock_get_user.return_value = self.mock_user
            mock_update.return_value = self.mock_user

            # Act
            result = await self.user_service.ensure_user_has_stripe_customer(1, self.mock_session)

            # Assert
            assert result == "cus_new123"
            mock_get_user.assert_called_once_with(self.mock_session, 1)
            self.mock_stripe_service.create_customer.assert_called_once_with(self.mock_user)
