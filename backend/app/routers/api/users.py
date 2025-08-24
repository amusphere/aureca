from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlmodel import Session

from app.database import get_session
from app.models.user import UserModel, UserWithSubscriptionModel
from app.schema import User
from app.services.auth import auth_user
from app.services.user_service import user_service

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserWithSubscriptionModel)
@cache(expire=300)  # 5 minutes cache as specified in requirements
async def get_current_user(user: User = Depends(auth_user), session: Session = Depends(get_session)):
    """
    Get current user information with subscription details.

    Returns user information including subscription status, plan details,
    and premium access information.

    This endpoint is cached for 5 minutes to optimize performance while
    ensuring subscription information remains reasonably fresh.
    """
    user_with_subscription = await user_service.get_user_with_subscription(user.id, session)
    return user_with_subscription


@router.get("/me/basic", response_model=UserModel)
async def get_current_user_basic(user: User = Depends(auth_user)):
    """
    Get basic current user information without subscription details.

    This endpoint provides the original user information format
    for backward compatibility.
    """
    return user
