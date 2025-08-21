"""
Integration tests for Stripe API endpoints.

This module tests that the minimal Stripe endpoints are properly registered
and accessible through the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestStripeEndpointsRegistration:
    """Test that Stripe endpoints are properly registered."""

    def test_stripe_health_endpoint_exists(self, client):
        """Test that the Stripe health endpoint is accessible."""
        response = client.get("/api/stripe/health")
        # Should return 200 regardless of Stripe configuration
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "status" in data

    def test_webhook_endpoint_exists(self, client):
        """Test that the webhook endpoint exists."""
        # This should return 400 (missing signature) but not 404 (not found)
        response = client.post("/api/stripe/webhook", data=b'{"test": "data"}')
        assert response.status_code == 400  # Missing signature, not 404
        assert "Missing Stripe signature" in response.json()["detail"]

    def test_stripe_endpoints_in_openapi_schema(self, client):
        """Test that Stripe endpoints are included in the OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check that minimal Stripe endpoints are in the schema
        assert "/api/stripe/health" in paths
        assert "/api/stripe/webhook" in paths

        # Check that the endpoints have the correct methods
        assert "get" in paths["/api/stripe/health"]
        assert "post" in paths["/api/stripe/webhook"]
