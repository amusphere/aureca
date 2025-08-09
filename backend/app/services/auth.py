from fastapi import Depends, HTTPException, status

from app.database import get_session
from app.schema import User
from app.utils.auth.clerk import (
    create_new_user,
    get_auth_sub,
    get_authed_user,
)


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
        user = create_new_user(sub, session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
