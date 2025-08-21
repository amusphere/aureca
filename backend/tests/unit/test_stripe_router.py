"""
Unit tests for Stripe API router endpoints.

This module tests the minimal Stripe router endpoints for webhook handling
and health monitoring. Payment and subscription management are handled
through Stripe's hosted solutions.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestStripeWebhook:
    """Test cases for Stripe webhook endpoint."""

    @patch("app.routers.api.stripe.stripe_service")
    @patch("app.routers.api.stripe.stripe_webhook_handler")
    def test_webhook_success(self, mock_webhook_handler, mock_stripe_service, client):
        """Test successful webhook processing."""
        # Setup mocks
        mock_event = {"id": "evt_test123", "type": "customer.subscription.created"}
        mock_stripe_service.verify_webhook_signature = AsyncMock(return_value=mock_event)
        mock_webhook_handler.handle_event = AsyncMock(return_value=True)

        # Make request
        response = client.post(
            "/api/stripe/webhook",
            data=b'{"id": "evt_test123"}',
            headers={"stripe-signature": "t=123,v1=signature"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify service calls
        mock_stripe_service.verify_webhook_signature.assert_called_once()
        mock_webhook_handler.handle_event.assert_called_once_with(mock_event)

    def test_webhook_missing_signature(self, client):
        """Test webhook processing with missing signature."""
        # Make request without signature header
        response = client.post(
            "/api/stripe/webhook",
            data=b'{"id": "evt_test123"}',
        )

        # Assertions
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]

    @patch("app.routers.api.stripe.stripe_service")
    def test_webhook_invalid_signature(self, mock_stripe_service, client):
        """Test webhook processing with invalid signature."""
        # Setup mocks
        from stripe.error import SignatureVerificationError

        mock_stripe_service.verify_webhook_signature = AsyncMock(
            side_effect=SignatureVerificationError("Invalid signature", "sig_header")
        )

        # Make request
        response = client.post(
            "/api/stripe/webhook",
            data=b'{"id": "evt_test123"}',
            headers={"stripe-signature": "invalid_signature"},
        )

        # Assertions
        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @patch("app.routers.api.stripe.stripe_service")
    @patch("app.routers.api.stripe.stripe_webhook_handler")
    def test_webhook_processing_failure(self, mock_webhook_handler, mock_stripe_service, client):
        """Test webhook processing failure."""
        # Setup mocks
        mock_event = {"id": "evt_test123", "type": "customer.subscription.created"}
        mock_stripe_service.verify_webhook_signature = AsyncMock(return_value=mock_event)
        mock_webhook_handler.handle_event = AsyncMock(return_value=False)

        # Make request
        response = client.post(
            "/api/stripe/webhook",
            data=b'{"id": "evt_test123"}',
            headers={"stripe-signature": "t=123,v1=signature"},
        )

        # Assertions
        assert response.status_code == 500
        assert "Failed to process webhook event" in response.json()["detail"]


class TestStripeHealth:
    """Test cases for Stripe health endpoint."""

    @patch("app.routers.api.stripe.stripe_service")
    def test_health_check_configured(self, mock_stripe_service, client):
        """Test health check when Stripe is configured."""
        # Setup mocks
        mock_stripe_service.is_configured.return_value = True
        mock_stripe_service.is_test_mode.return_value = True
        mock_stripe_service.get_publishable_key.return_value = "pk_test_123"
        mock_stripe_service.verify_api_connection = AsyncMock(return_value=True)

        # Make request
        response = client.get("/api/stripe/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["test_mode"] is True
        assert data["publishable_key_available"] is True
        assert data["api_connection"] is True
        assert data["status"] == "healthy"

    @patch("app.routers.api.stripe.stripe_service")
    def test_health_check_not_configured(self, mock_stripe_service, client):
        """Test health check when Stripe is not configured."""
        # Setup mocks
        mock_stripe_service.is_configured.return_value = False
        mock_stripe_service.get_publishable_key.return_value = None

        # Make request
        response = client.get("/api/stripe/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert data["test_mode"] is False
        assert data["publishable_key_available"] is False
        assert data["api_connection"] is False
        assert data["status"] == "not_configured"
