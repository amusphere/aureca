from app.database import get_session
from app.models.mail import DraftModel
from app.schema import User
from app.services.auth import auth_user
from app.services.gmail_service import get_authenticated_gmail_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/mail", tags=["Mail"])


@router.get("/drafts/{draft_id}", response_model=DraftModel)
async def get_draft_endpoint(
    draft_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """指定したドラフトの詳細を取得"""
    async with get_authenticated_gmail_service(user, session) as gmail_service:
        draft = await gmail_service.get_draft(draft_id)

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found"
        )

    return draft
