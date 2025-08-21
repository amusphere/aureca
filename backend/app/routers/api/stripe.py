"""
Stripe API router for webhook handling and health monitoring.

This router provides minimal endpoints for Stripe webhook processing
and service health monitoring. Payment and subscription management
are handled directly through Stripe's hosted solutions.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from stripe.error import SignatureVerificationError

from app.services.stripe_service import stripe_service
from app.services.stripe_webhook_handler import stripe_webhook_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.get("/health")
async def stripe_health_check() -> dict[str, Any]:
    """
    Check Stripe service health and configuration status.

    Returns:
        Dict containing Stripe service status information
    """
    try:
        is_configured = stripe_service.is_configured()
        is_test_mode = stripe_service.is_test_mode() if is_configured else False

        status = {
            "configured": is_configured,
            "test_mode": is_test_mode,
            "publishable_key_available": bool(stripe_service.get_publishable_key()),
        }

        if is_configured:
            # Test API connection
            connection_ok = await stripe_service.verify_api_connection()
            status["api_connection"] = connection_ok

            if connection_ok:
                status["status"] = "healthy"
            else:
                status["status"] = "configured_but_connection_failed"
        else:
            status["status"] = "not_configured"
            status["api_connection"] = False

        return status

    except Exception as e:
        logger.error(f"Error checking Stripe health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check Stripe service health") from e


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, str]:
    """
    Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe and processes them
    to keep the local database synchronized with Stripe's state.

    Args:
        request: The FastAPI request object containing the webhook payload

    Returns:
        Dict with success status

    Raises:
        HTTPException: If webhook processing fails
    """
    try:
        # Get the raw body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            logger.error("Missing Stripe signature header")
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Verify the webhook signature and construct the event
        try:
            event = await stripe_service.verify_webhook_signature(payload, signature)
        except SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature") from e
        except ValueError as e:
            logger.error(f"Webhook configuration error: {e}")
            raise HTTPException(status_code=500, detail="Webhook configuration error") from e

        # Process the event
        success = await stripe_webhook_handler.handle_event(event)

        if not success:
            logger.error(f"Failed to process webhook event {event.get('id', 'unknown')}")
            raise HTTPException(status_code=500, detail="Failed to process webhook event")

        logger.info(f"Successfully processed webhook event {event.get('id', 'unknown')}")
        return {"status": "success"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
