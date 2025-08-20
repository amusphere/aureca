import logging
import sys

import httpx
from clerk_backend_api import AuthenticateRequestOptions, Clerk
from clerk_backend_api import User as ClerkUser
from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from sqlmodel import Session

from app.repositories.user import get_user_br_column
from app.schema import User

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

from app.config.auth import AuthConfig, ClerkConfig

CLERK_SECRET_KEY = ClerkConfig.SECRET_KEY
AUTHORIZED_PARTIES = AuthConfig.get_authorized_parties()

security = HTTPBearer()


async def get_auth_sub(request: Request, credentials=Depends(security)) -> str | None:
    httpx_req = httpx.Request(
        method=request.method,
        url=str(request.url),
        headers={
            "Authorization": f"Bearer {credentials.credentials}",
        },
    )

    sdk = Clerk(bearer_auth=CLERK_SECRET_KEY)
    request_state = sdk.authenticate_request(
        httpx_req,
        AuthenticateRequestOptions(authorized_parties=AUTHORIZED_PARTIES),
    )

    if request_state.is_signed_in:
        return request_state.payload["sub"]
    else:
        logger.error("Not authenticated: %s", request_state.reason)
        return None


async def get_authed_user(sub: str, session: Session) -> User | None:
    user = get_user_br_column(session, sub, "clerk_sub")
    return user


def create_new_user(sub: str, session: Session) -> User:
    sdk = Clerk(bearer_auth=CLERK_SECRET_KEY)
    clerk_user: ClerkUser = sdk.users.get(user_id=sub)

    email = None
    for email_address in clerk_user.email_addresses:
        if email_address.id == clerk_user.primary_email_address_id:
            email = email_address.email_address
            break

    user = User(
        email=email,
        name=clerk_user.username,
        clerk_sub=sub,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_clerk_user(clerk_sub: str) -> None:
    """Delete user from Clerk"""
    try:
        sdk = Clerk(bearer_auth=CLERK_SECRET_KEY)
        sdk.users.delete(user_id=clerk_sub)
        logger.info(f"Successfully deleted user from Clerk: {clerk_sub}")
    except Exception as e:
        logger.error(f"Failed to delete user from Clerk: {clerk_sub}, error: {e}")
        # Don't raise the exception to avoid blocking local database deletion
        # The user will be deleted from local database even if Clerk deletion fails
