import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.models.ai_assistant import (
    AIRequestModel,
    AIResponseModel,
    GeneratedTasksBySourceModel,
)
from app.models.ai_chat_usage import AIChatUsageResponse
from app.schema import User
from app.services.ai import AIHub
from app.services.ai_chat_usage_service import AIChatUsageService
from app.services.ai_task_service import AiTaskService
from app.services.auth import auth_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def _safe_get_reset_time(usage_service: AIChatUsageService) -> str:
    """Safely get reset time, returning 'unknown' if there's an error."""
    try:
        return usage_service._get_reset_time()
    except Exception:
        return "unknown"


@router.post("/process", response_model=AIResponseModel)
async def process_ai_request_endpoint(
    request: AIRequestModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AIアシスタントにリクエストを送信して処理結果を取得"""
    # Initialize usage service with the injected session
    usage_service = AIChatUsageService(session=session)

    try:
        # Check usage limits before processing
        await usage_service.check_usage_limit(user)

        # Process AI request
        hub = AIHub(user.id, session)
        result = await hub.process_request(prompt=request.prompt, current_user=user)

        # Increment usage count after successful processing
        await usage_service.increment_usage(user)

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (403, 429) as they contain proper error responses
        raise
    except Exception:
        # Handle unexpected errors during AI processing
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "reset_time": _safe_get_reset_time(usage_service),
            },
        ) from None


@router.post("/generate-from-all", response_model=GeneratedTasksBySourceModel)
async def generate_tasks_from_all_endpoint(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """全ての情報源からタスクを自動生成"""
    ai_task_service = AiTaskService(session=session, user_id=user.id)
    generated_tasks = await ai_task_service.generate_tasks_from_all_sources(user=user)

    return generated_tasks


@router.get("/usage", response_model=AIChatUsageResponse)
async def get_ai_chat_usage_endpoint(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AI Chat利用状況を取得"""
    # Create service with the session that's already injected
    usage_service = AIChatUsageService(session=session)

    try:
        usage_stats = await usage_service.check_usage_limit(user)
        # Extract only the fields needed for the response model
        response_data = {
            "remaining_count": usage_stats["remaining_count"],
            "daily_limit": usage_stats["daily_limit"],
            "reset_time": usage_stats["reset_time"],
            "can_use_chat": usage_stats["can_use_chat"],
        }
        return AIChatUsageResponse(**response_data)
    except HTTPException:
        # Re-raise HTTP exceptions (403, 429) as they contain proper error responses
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error in get_ai_chat_usage_endpoint: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "reset_time": _safe_get_reset_time(usage_service),
            },
        ) from e


@router.post("/usage/increment", response_model=AIChatUsageResponse)
async def increment_ai_chat_usage_endpoint(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AI Chat利用回数を記録（内部API）"""
    usage_service = AIChatUsageService(session=session)

    try:
        updated_stats = await usage_service.increment_usage(user)
        # Extract only the fields needed for the response model
        response_data = {
            "remaining_count": updated_stats["remaining_count"],
            "daily_limit": updated_stats["daily_limit"],
            "reset_time": updated_stats["reset_time"],
            "can_use_chat": updated_stats["can_use_chat"],
        }
        return AIChatUsageResponse(**response_data)
    except HTTPException:
        # Re-raise HTTP exceptions (403, 429) as they contain proper error responses
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error in increment_ai_chat_usage_endpoint: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "reset_time": _safe_get_reset_time(usage_service),
            },
        ) from e
