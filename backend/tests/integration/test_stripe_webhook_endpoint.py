"""
Integration tests for Stripe webhook endpoint.

Tests the webhook endpoint integration with FastAPI and request handling.
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestStripeWebhookEndpoint:
    """Test cases for Stripe webhook endpoint."""

    def test_webhook_missing_signature(self):
        """Test webhook endpoint with missing signature header."""
        payload = {"type": "customer.subscription.created"}

        response = client.post("/api/stripe/webhook", json=payload)

        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]

    @patch("app.services.stripe_service.stripe_service.verify_webhook_signature")
    @patch("app.services.stripe_webhook_handler.stripe_webhook_handler.handle_event")
    def test_webhook_success(self, mock_handle_event, mock_verify_signature):
        """Test successful webhook processing."""
        # Mock event
        mock_event = {
            "id": "evt_test_123",
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_test_123"}},
        }

        # Mock successful verification and handling
        mock_verify_signature.return_value = mock_event
        mock_handle_event.return_value = True

        payload = json.dumps({"type": "customer.subscription.created"})

        response = client.post("/api/stripe/webhook", data=payload, headers={"stripe-signature": "t=123,v1=signature"})

        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_verify_signature.assert_called_once()
        mock_handle_event.assert_called_once_with(mock_event)

    @patch("app.services.stripe_service.stripe_service.verify_webhook_signature")
    def test_webhook_invalid_signature(self, mock_verify_signature):
        """Test webhook with invalid signature."""
        from stripe.error import SignatureVerificationError

        # Mock signature verification failure
        mock_verify_signature.side_effect = SignatureVerificationError("Invalid signature", "sig_header")

        payload = json.dumps({"type": "customer.subscription.created"})

        response = client.post("/api/stripe/webhook", data=payload, headers={"stripe-signature": "t=123,v1=invalid"})

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @patch("app.services.stripe_service.stripe_service.verify_webhook_signature")
    @patch("app.services.stripe_webhook_handler.stripe_webhook_handler.handle_event")
    def test_webhook_processing_failure(self, mock_handle_event, mock_verify_signature):
        """Test webhook processing failure."""
        # Mock event
        mock_event = {
            "id": "evt_test_123",
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_test_123"}},
        }

        # Mock successful verification but failed handling
        mock_verify_signature.return_value = mock_event
        mock_handle_event.return_value = False

        payload = json.dumps({"type": "customer.subscription.created"})

        response = client.post("/api/stripe/webhook", data=payload, headers={"stripe-signature": "t=123,v1=signature"})

        assert response.status_code == 500
        assert "Failed to process webhook event" in response.json()["detail"]

    @patch("app.services.stripe_service.stripe_service.verify_webhook_signature")
    def test_webhook_configuration_error(self, mock_verify_signature):
        """Test webhook with configuration error."""
        # Mock configuration error
        mock_verify_signature.side_effect = ValueError("Webhook configuration error")

        payload = json.dumps({"type": "customer.subscription.created"})

        response = client.post("/api/stripe/webhook", data=payload, headers={"stripe-signature": "t=123,v1=signature"})

        assert response.status_code == 500
        assert "Webhook configuration error" in response.json()["detail"]
