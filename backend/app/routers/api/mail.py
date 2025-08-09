from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.google_mail import DraftModel
from app.repositories.task_source import get_task_source_by_uuid
from app.schema import SourceType, User
from app.services.ai_task_service import AiTaskService
from app.services.auth import auth_user
from app.services.gmail_service import get_authenticated_gmail_service

router = APIRouter(prefix="/mail", tags=["Mail"])


@router.get("/drafts/{task_source_uuid}", response_model=DraftModel)
async def get_draft_by_task_source_endpoint(
    task_source_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """指定したタスクソースに関連するメールのドラフトを取得"""
    # タスクソースを取得
    task_source = get_task_source_by_uuid(session, task_source_uuid)

    if not task_source or task_source.task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task source not found")

    # メールソースでない場合は404
    if task_source.source_type != SourceType.EMAIL:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task source is not an email source",
        )

    # メールIDがない場合は404
    if not task_source.source_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email source ID is missing")

    # 該当メールのドラフトを取得
    async with get_authenticated_gmail_service(user, session) as gmail_service:
        drafts = await gmail_service.get_drafts_by_thread_id(task_source.source_id)

        if not drafts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No draft found for this email",
            )

        # 最新のドラフトを返す（複数ある場合）
        return drafts[0]


@router.delete("/drafts/{task_source_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft_by_task_source_endpoint(
    task_source_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """指定したタスクソースに関連するメールのドラフトを削除"""
    # タスクソースを取得
    task_source = get_task_source_by_uuid(session, task_source_uuid)

    if not task_source or task_source.task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task source not found")

    # メールソースでない場合は404
    if task_source.source_type != SourceType.EMAIL:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task source is not an email source",
        )

    # メールIDがない場合は404
    if not task_source.source_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email source ID is missing")

    # 該当メールのドラフトを削除
    async with get_authenticated_gmail_service(user, session) as gmail_service:
        await gmail_service.delete_drafts_by_thread_id(task_source.source_id)


@router.post("/drafts/{task_source_uuid}", response_model=DraftModel)
async def generate_email_reply_draft_endpoint(
    task_source_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """TaskSourceからメール返信下書きを生成"""
    ai_task_service = AiTaskService(session=session, user_id=user.id)
    reply_draft = await ai_task_service.generate_email_reply_draft(task_source_uuid=task_source_uuid, user=user)

    if not reply_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TaskSource not found or not an email source",
        )

    return reply_draft
