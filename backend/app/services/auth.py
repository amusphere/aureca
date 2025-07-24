import os

from app.repositories.user import delete_user
from app.schema import User
from app.utils.auth.clerk import (
    create_new_user,
    delete_clerk_user,
    get_auth_sub,
    get_authed_user,
)
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

TOKEN_EXPIRE_MINUTES = 30
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def user_sub(sub=Depends(get_auth_sub)) -> str | None:
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return sub


async def auth_user(sub=Depends(get_auth_sub)) -> User:
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = await get_authed_user(sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def add_new_user(sub: str) -> User:
    user = create_new_user(sub)
    return user


def delete_current_user(user: User, session: Session) -> None:
    """Delete the current user and all related data"""
    delete_clerk_user(user.clerk_sub)
    delete_user(session, user)
