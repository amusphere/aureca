"""
Stripe API router for subscription management.

This router provides endpoints for Stripe-related operations including
customer portal session creation for subscription management.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.database import get_session
from app.schema import User
from app.services.auth import auth_user
from app.services.stripe_service import StripeService
from app.services.user_service import user_service
from app.utils.exceptions import (
    StripeConfigurationException,
    StripeServiceException,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe")


class PortalSessionRequest(BaseModel):
    """Request model for creating customer portal session."""

    return_url: str


class PortalSessionResponse(BaseModel):
    """Response model for customer portal session."""

    url: str


@router.post("/create-portal-session", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    user: User = Depends(auth_user),
    session: Session = Depends(get_session),
) -> PortalSessionResponse:
    """
    Create a Stripe Customer Portal session for subscription management.

    This endpoint allows authenticated users to access the Stripe Customer Portal
    where they can manage their subscriptions, update payment methods, view
    billing history, and cancel subscriptions.

    Args:
        request: Portal session request containing return URL
        user: Authenticated user from auth dependency
        session: Database session

    Returns:
        PortalSessionResponse: Contains the portal session URL

    Raises:
        HTTPException: 400 if Stripe is not configured
        HTTPException: 404 if user doesn't have a Stripe customer
        HTTPException: 500 if portal session creation fails
    """
    try:
        # Initialize Stripe service
        stripe_service = StripeService()

        # Ensure user has a Stripe customer ID
        user_with_stripe = await user_service.ensure_stripe_customer(user.id, session)

        if not user_with_stripe.stripe_customer_id:
            logger.error(f"User {user.id} does not have a Stripe customer ID after ensure_stripe_customer")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer account not found. Please contact support.",
            )

        # Create customer portal session
        portal_session = await stripe_service.create_customer_portal_session(
            customer_id=user_with_stripe.stripe_customer_id,
            return_url=request.return_url,
        )

        logger.info(
            f"Created customer portal session for user {user.id}",
            extra={
                "user_id": user.id,
                "stripe_customer_id": user_with_stripe.stripe_customer_id,
                "portal_session_id": portal_session.id,
                "return_url": request.return_url,
            },
        )

        return PortalSessionResponse(url=portal_session.url)

    except StripeConfigurationException as e:
        logger.error(f"Stripe configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment service is not properly configured. Please contact support.",
        ) from e

    except StripeServiceException as e:
        logger.error(f"Stripe service error creating portal session for user {user.id}: {e}")

        # Provide user-friendly error messages based on error code
        if e.error_code == "STRIPE_INVALID_REQUEST":
            detail = "Unable to access customer portal. Please contact support."
        elif e.error_code == "STRIPE_PORTAL_CREATE_ERROR":
            detail = "Failed to create customer portal session. Please try again later."
        else:
            detail = "An error occurred while accessing the customer portal. Please try again later."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e

    except Exception as e:
        logger.error(f"Unexpected error creating portal session for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get("/config")
async def get_stripe_config() -> dict[str, Any]:
    """
    Get Stripe configuration for frontend use.

    Returns public Stripe configuration including publishable key
    and test mode status for frontend integration.

    Returns:
        dict: Stripe configuration including publishable key and test mode status

    Raises:
        HTTPException: 400 if Stripe is not configured
    """
    try:
        stripe_service = StripeService()

        if not stripe_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment service is not configured.",
            )

        return {
            "publishable_key": stripe_service.get_publishable_key(),
            "test_mode": stripe_service.is_test_mode(),
        }

    except StripeConfigurationException as e:
        logger.error(f"Stripe configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment service is not properly configured.",
        ) from e

    except Exception as e:
        logger.error(f"Unexpected error getting Stripe config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e
