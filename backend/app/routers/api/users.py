import os

from app.database import get_session
from app.models.user import UserModel
from app.schema import User
from app.services.auth import add_new_user, auth_user, delete_current_user, user_sub
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/users")

AUTH_SYSTEM = os.getenv("AUTH_SYSTEM")


@router.post("", response_model=UserModel)
async def create_user(sub: str = Depends(user_sub)):
    """Create new user by clerk"""
    if AUTH_SYSTEM == "email_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/Password authentication system does not support user creation.",
        )
    return add_new_user(sub)


@router.delete("")
async def delete_current_user_endpoint(
    user: User = Depends(auth_user), session: Session = Depends(get_session)
):
    """Delete current user and all related data"""
    delete_current_user(user, session)
    return {"message": "User deleted successfully"}


@router.get("/me", response_model=UserModel)
async def get_current_user(user: User = Depends(auth_user)):
    return user
