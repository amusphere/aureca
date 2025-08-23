import logging

from fastapi import Depends, HTTPException, status

from app.database import get_session
from app.schema import User
from app.services.user_service import user_service
from app.utils.auth.clerk import (
    get_auth_sub,
    get_authed_user,
)

logger = logging.getLogger(__name__)


async def user_sub(sub=Depends(get_auth_sub)) -> str | None:
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return sub


async def auth_user(sub=Depends(get_auth_sub), session=Depends(get_session)) -> User:
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = await get_authed_user(sub, session)

    if user is None:
        user = user_service.create_new_user(sub, session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    try:
        if user_service.stripe_service.is_configured() and not user.stripe_customer_id:
            await user_service.ensure_stripe_customer(user, session)
    except Exception as e:
        # Log the error but don't fail user authentication
        # The Stripe customer can be created later when needed
        logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")

    return user
