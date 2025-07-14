from app.database import get_session
from app.models.ai_assistant import (
    AIRequestModel,
    AIResponseModel,
    GenerateTasksFromEmailsResponseModel,
)
from app.models.google_mail import DraftModel
from app.schema import User
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai_task_service import AiTaskService
from app.services.auth import auth_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/process", response_model=AIResponseModel)
async def process_ai_request_endpoint(
    request: AIRequestModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AIアシスタントにリクエストを送信して処理結果を取得"""
    orchestrator = AIOrchestrator(user.id, session)
    result = await orchestrator.process_request(
        prompt=request.prompt, current_user=user
    )

    return result


@router.post(
    "/generate-from-emails",
    response_model=GenerateTasksFromEmailsResponseModel,
)
async def generate_tasks_from_emails_endpoint(
    max_emails: int = 10,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """新着メールからタスクを自動生成"""
    ai_task_service = AiTaskService(session=session, user_id=user.id)
    generated_tasks = await ai_task_service.generate_tasks_from_new_emails(
        user=user, max_emails=max_emails
    )

    return {
        "success": True,
        "message": f"{len(generated_tasks)}個のタスクを生成しました",
        "generated_tasks": generated_tasks,
    }


@router.post(
    "/generate-email-reply-draft/{task_source_uuid}",
    response_model=DraftModel,
)
async def generate_email_reply_draft_endpoint(
    task_source_uuid: str,
    create_gmail_draft: bool = False,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """TaskSourceからメール返信下書きを生成"""
    ai_task_service = AiTaskService(session=session, user_id=user.id)
    reply_draft = await ai_task_service.generate_email_reply_draft(
        task_source_uuid=task_source_uuid,
        user=user,
        create_gmail_draft=create_gmail_draft,
    )

    if not reply_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TaskSource not found or not an email source",
        )

    return reply_draft
