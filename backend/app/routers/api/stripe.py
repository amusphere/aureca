"""
Stripe API router for handling subscription and payment operations.

This router provides endpoints for Stripe operations including
customer management, subscription handling, and webhook processing.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.stripe_service import stripe_service

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
        raise HTTPException(status_code=500, detail="Failed to check Stripe service health")
