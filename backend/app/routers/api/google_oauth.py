from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.google_oauth import (
    GoogleAuthResponse,
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
)
from app.schema import User
from app.services.auth import auth_user
from app.services.google_oauth import GoogleOauthService

router = APIRouter(prefix="/google")


@router.get("/auth-url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(user: User = Depends(auth_user)):
    """Google OAuth認証URLを生成"""
    try:
        oauth_service = GoogleOauthService()
        auth_url = oauth_service.get_auth_url(user.id)
        return GoogleAuthUrlResponse(auth_url=auth_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}",
        )


@router.post("/callback", response_model=GoogleAuthResponse)
async def google_oauth_callback(
    request: GoogleCallbackRequest,
    session: Session = Depends(get_session),
):
    """Google OAuth認証コールバック処理"""
    try:
        oauth_service = GoogleOauthService(session=session)
        oauth_service.save_oauth_tokens(request)

        return GoogleAuthResponse(
            success=True, message="Google account connected successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process callback: {str(e)}",
        )


@router.delete("/disconnect")
async def disconnect_google_account(
    user: User = Depends(auth_user),
    session: Session = Depends(get_session),
):
    """Google アカウントの連携を解除"""
    try:
        calendar_service = GoogleOauthService(session)
        calendar_service.revoke_access(user.id)

        return GoogleAuthResponse(
            success=True, message="Google account disconnected successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect account: {str(e)}",
        )


@router.get("/status")
async def get_google_connection_status(
    user: User = Depends(auth_user),
    session: Session = Depends(get_session),
):
    """Google連携状況を確認"""
    try:
        calendar_service = GoogleOauthService(session)
        credentials = calendar_service.get_credentials(user.id)

        return {"connected": credentials is not None, "user_id": user.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check connection status: {str(e)}",
        )
