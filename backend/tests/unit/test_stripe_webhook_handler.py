"""
Unit tests for Stripe webhook handler.

Tests the webhook event processing logic and database synchronization.
"""

from unittest.mock import Mock, patch

import pytest

from app.services.stripe_webhook_handler import StripeWebhookHandler


class TestStripeWebhookHandler:
    """Test cases for StripeWebhookHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = StripeWebhookHandler()

    @pytest.mark.asyncio
    async def test_handle_event_customer_subscription_created(self):
        """Test handling customer.subscription.created event."""
        # Mock event data
        event = {
            "id": "evt_test_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active",
                    "current_period_start": 1640995200,
                    "current_period_end": 1643673600,
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "trial_start": None,
                    "trial_end": None,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_test_123",
                                    "nickname": "Premium Plan",
                                    "metadata": {},
                                    "product": {"name": "Premium"},
                                }
                            }
                        ]
                    },
                }
            },
        }

        with (
            patch("app.services.stripe_webhook_handler.get_session") as mock_get_session,
            patch("app.repositories.user.get_user_br_column") as mock_get_user,
            patch("app.repositories.subscription.get_subscription_by_stripe_id") as mock_get_sub,
            patch("app.repositories.subscription.create_subscription") as mock_create_sub,
        ):
            # Mock session context manager
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock user found
            mock_user = Mock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user

            # Mock no existing subscription
            mock_get_sub.return_value = None

            # Mock successful creation
            mock_subscription = Mock()
            mock_create_sub.return_value = mock_subscription

            # Test the handler
            result = await self.handler.handle_customer_subscription_created(event)

            # Assertions
            assert result is True
            mock_get_user.assert_called_once_with(mock_session, "cus_test_123", "stripe_customer_id")
            mock_get_sub.assert_called_once_with(mock_session, "sub_test_123")
            mock_create_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_customer_subscription_updated(self):
        """Test handling customer.subscription.updated event."""
        # Mock event data
        event = {
            "id": "evt_test_124",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "canceled",
                    "current_period_start": 1640995200,
                    "current_period_end": 1643673600,
                    "cancel_at_period_end": True,
                    "canceled_at": 1642000000,
                    "trial_start": None,
                    "trial_end": None,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_test_123",
                                    "nickname": "Premium Plan",
                                    "metadata": {},
                                    "product": {"name": "Premium"},
                                }
                            }
                        ]
                    },
                }
            },
        }

        with (
            patch("app.services.stripe_webhook_handler.get_session") as mock_get_session,
            patch("app.repositories.subscription.update_subscription_by_stripe_id") as mock_update_sub,
        ):
            # Mock session context manager
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock successful update
            mock_subscription = Mock()
            mock_update_sub.return_value = mock_subscription

            # Test the handler
            result = await self.handler.handle_customer_subscription_updated(event)

            # Assertions
            assert result is True
            mock_update_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_customer_subscription_deleted(self):
        """Test handling customer.subscription.deleted event."""
        # Mock event data
        event = {
            "id": "evt_test_125",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_test_123", "customer": "cus_test_123", "status": "canceled"}},
        }

        with (
            patch("app.services.stripe_webhook_handler.get_session") as mock_get_session,
            patch("app.repositories.subscription.deactivate_subscription_by_stripe_id") as mock_deactivate_sub,
        ):
            # Mock session context manager
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock successful deactivation
            mock_subscription = Mock()
            mock_deactivate_sub.return_value = mock_subscription

            # Test the handler
            result = await self.handler.handle_customer_subscription_deleted(event)

            # Assertions
            assert result is True
            mock_deactivate_sub.assert_called_once_with(mock_session, "sub_test_123")

    @pytest.mark.asyncio
    async def test_handle_event_invoice_payment_succeeded(self):
        """Test handling invoice.payment_succeeded event."""
        # Mock event data
        event = {
            "id": "evt_test_126",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"id": "in_test_123", "subscription": "sub_test_123", "status": "paid"}},
        }

        with (
            patch("app.services.stripe_webhook_handler.get_session") as mock_get_session,
            patch("app.repositories.subscription.update_subscription_by_stripe_id") as mock_update_sub,
            patch("stripe.Subscription.retrieve") as mock_stripe_retrieve,
        ):
            # Mock session context manager
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock Stripe subscription
            mock_stripe_sub = Mock()
            mock_stripe_sub.status = "active"
            mock_stripe_sub.current_period_start = 1640995200
            mock_stripe_sub.current_period_end = 1643673600
            mock_stripe_sub.cancel_at_period_end = False
            mock_stripe_retrieve.return_value = mock_stripe_sub

            # Mock successful update
            mock_subscription = Mock()
            mock_update_sub.return_value = mock_subscription

            # Test the handler
            result = await self.handler.handle_invoice_payment_succeeded(event)

            # Assertions
            assert result is True
            mock_stripe_retrieve.assert_called_once_with("sub_test_123")
            mock_update_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_invoice_payment_failed(self):
        """Test handling invoice.payment_failed event."""
        # Mock event data
        event = {
            "id": "evt_test_127",
            "type": "invoice.payment_failed",
            "data": {"object": {"id": "in_test_124", "subscription": "sub_test_123", "status": "open"}},
        }

        with (
            patch("app.services.stripe_webhook_handler.get_session") as mock_get_session,
            patch("app.repositories.subscription.update_subscription_by_stripe_id") as mock_update_sub,
            patch("stripe.Subscription.retrieve") as mock_stripe_retrieve,
        ):
            # Mock session context manager
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None

            # Mock Stripe subscription
            mock_stripe_sub = Mock()
            mock_stripe_sub.status = "past_due"
            mock_stripe_retrieve.return_value = mock_stripe_sub

            # Mock successful update
            mock_subscription = Mock()
            mock_update_sub.return_value = mock_subscription

            # Test the handler
            result = await self.handler.handle_invoice_payment_failed(event)

            # Assertions
            assert result is True
            mock_stripe_retrieve.assert_called_once_with("sub_test_123")
            mock_update_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_unhandled_type(self):
        """Test handling unhandled event types."""
        # Mock event data
        event = {"id": "evt_test_128", "type": "customer.created", "data": {"object": {"id": "cus_test_123"}}}

        # Test the handler
        result = await self.handler.handle_event(event)

        # Should return True for unhandled events to avoid retries
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_event_exception(self):
        """Test handling exceptions during event processing."""
        # Mock event data
        event = {
            "id": "evt_test_129",
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_test_123"}},
        }

        with patch.object(self.handler, "handle_customer_subscription_created", side_effect=Exception("Test error")):
            # Test the handler
            result = await self.handler.handle_event(event)

            # Should return False on exception
            assert result is False

    def test_extract_plan_name_from_metadata(self):
        """Test extracting plan name from price metadata."""
        subscription_data = {
            "items": {
                "data": [
                    {
                        "price": {
                            "id": "price_test_123",
                            "metadata": {"plan_name": "Premium Plan"},
                            "nickname": "Premium",
                            "product": {"name": "Product Name"},
                        }
                    }
                ]
            }
        }

        result = self.handler._extract_plan_name(subscription_data)
        assert result == "Premium Plan"

    def test_extract_plan_name_from_nickname(self):
        """Test extracting plan name from price nickname."""
        subscription_data = {
            "items": {
                "data": [
                    {
                        "price": {
                            "id": "price_test_123",
                            "metadata": {},
                            "nickname": "Premium",
                            "product": {"name": "Product Name"},
                        }
                    }
                ]
            }
        }

        result = self.handler._extract_plan_name(subscription_data)
        assert result == "Premium"

    def test_extract_plan_name_from_product(self):
        """Test extracting plan name from product name."""
        subscription_data = {
            "items": {
                "data": [
                    {
                        "price": {
                            "id": "price_test_123",
                            "metadata": {},
                            "nickname": None,
                            "product": {"name": "Product Name"},
                        }
                    }
                ]
            }
        }

        result = self.handler._extract_plan_name(subscription_data)
        assert result == "Product Name"

    def test_extract_plan_name_fallback(self):
        """Test extracting plan name fallback to price ID."""
        subscription_data = {
            "items": {"data": [{"price": {"id": "price_test_123", "metadata": {}, "nickname": None, "product": {}}}]}
        }

        result = self.handler._extract_plan_name(subscription_data)
        assert result == "Plan price_test_123"
