from app.database import get_session
from app.models.ai_assistant import (
    AIRequestModel,
    AIResponseModel,
    GeneratedTaskModel,
)
from app.schema import User
from app.services.ai import AIHub
from app.services.ai_task_service import AiTaskService
from app.services.auth import auth_user
from fastapi import APIRouter, Depends
from sqlmodel import Session

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/process", response_model=AIResponseModel)
async def process_ai_request_endpoint(
    request: AIRequestModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AIアシスタントにリクエストを送信して処理結果を取得"""
    hub = AIHub(user.id, session)
    result = await hub.process_request(prompt=request.prompt, current_user=user)

    return result


@router.post("/generate-from-emails", response_model=list[GeneratedTaskModel])
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

    return generated_tasks


@router.post("/generate-from-calendar", response_model=list[GeneratedTaskModel])
async def generate_tasks_from_calendar_endpoint(
    days_ahead: int = 7,
    max_events: int = 20,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """カレンダーイベントからタスクを自動生成"""
    ai_task_service = AiTaskService(session=session, user_id=user.id)
    generated_tasks = await ai_task_service.generate_tasks_from_calendar_events(
        user=user, days_ahead=days_ahead, max_events=max_events
    )

    return generated_tasks
