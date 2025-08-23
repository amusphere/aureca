"""
Stripe API router for webhook handling and health monitoring.

This router provides minimal endpoints for Stripe webhook processing
and service health monitoring. Payment and subscription management
are handled directly through Stripe's hosted solutions.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.config.logging import log_security_event
from app.services.stripe_service import stripe_service
from app.services.stripe_webhook_handler import stripe_webhook_handler
from app.utils.exceptions import (
    StripeConfigurationException,
    StripeServiceException,
    StripeSignatureException,
    StripeWebhookException,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.get("/health")
async def stripe_health_check() -> dict[str, Any]:
    """
    Check Stripe service health and configuration status.

    Returns:
        Dict containing Stripe service status information

    Raises:
        HTTPException: If health check fails
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
            try:
                # Test API connection
                connection_ok = await stripe_service.verify_api_connection()
                status["api_connection"] = connection_ok

                if connection_ok:
                    status["status"] = "healthy"
                else:
                    status["status"] = "configured_but_connection_failed"
            except StripeConfigurationException as e:
                logger.error(f"Stripe configuration error during health check: {e}")
                status["status"] = "configuration_error"
                status["api_connection"] = False
                status["error"] = e.user_message
            except StripeServiceException as e:
                logger.error(f"Stripe service error during health check: {e}")
                status["status"] = "service_error"
                status["api_connection"] = False
                status["error"] = e.user_message
        else:
            status["status"] = "not_configured"
            status["api_connection"] = False

        logger.info(
            f"Stripe health check completed: {status['status']}",
            extra={
                "stripe_status": status["status"],
                "configured": is_configured,
                "test_mode": is_test_mode,
                "operation": "health_check",
            },
        )

        return status

    except (StripeConfigurationException, StripeServiceException):
        # These are already handled above
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking Stripe health: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check Stripe service health. Please try again later.",
        ) from e


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, str]:
    """
    Handle Stripe webhook events with comprehensive error handling.

    This endpoint receives webhook events from Stripe and processes them
    to keep the local database synchronized with Stripe's state.

    Args:
        request: The FastAPI request object containing the webhook payload

    Returns:
        Dict with success status

    Raises:
        HTTPException: If webhook processing fails
    """
    event_id = "unknown"
    event_type = "unknown"
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        # Get the raw body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            log_security_event(
                event_type="webhook_missing_signature",
                message="Webhook request missing Stripe signature header",
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Verify the webhook signature and construct the event
        try:
            event = await stripe_service.verify_webhook_signature(payload, signature)
            event_id = event.get("id", "unknown")
            event_type = event.get("type", "unknown")

        except StripeSignatureException as e:
            log_security_event(
                event_type="webhook_invalid_signature",
                message=f"Webhook signature verification failed: {e.message}",
                details=e.details,
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=400, detail="Invalid signature") from e

        except StripeConfigurationException as e:
            logger.error(f"Webhook configuration error: {e}")
            raise HTTPException(status_code=500, detail="Webhook configuration error") from e

        except StripeServiceException as e:
            logger.error(f"Webhook service error: {e}")
            raise HTTPException(status_code=500, detail="Webhook service error") from e

        # Process the event
        try:
            success = await stripe_webhook_handler.handle_event(event)

            if not success:
                logger.error(
                    f"Failed to process webhook event {event_id}",
                    extra={
                        "event_id": event_id,
                        "event_type": event_type,
                        "operation": "webhook_processing",
                    },
                )
                raise HTTPException(status_code=500, detail="Failed to process webhook event")

            logger.info(
                f"Successfully processed webhook event {event_id}",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "operation": "webhook_processing",
                },
            )
            return {"status": "success"}

        except StripeWebhookException as e:
            logger.error(
                f"Webhook processing failed: {e.message}",
                extra={
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "retry_count": e.retry_count,
                    "error_code": e.error_code,
                },
            )
            # Return 500 to trigger Stripe's retry mechanism
            raise HTTPException(status_code=500, detail=e.user_message) from e

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing webhook: {e}",
            extra={
                "event_id": event_id,
                "event_type": event_type,
                "client_ip": client_ip,
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please contact support if this persists.",
        ) from e
