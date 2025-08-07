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
from app.services.ai.core.hub import AIHub
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
        # 高速な利用可否チェック
        can_use = await usage_service.can_use_chat(user)
        if not can_use:
            # 詳細な制限チェックでエラー情報を取得
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
    except Exception as e:
        logger.error(f"Error processing AI request for user {user.id}: {e}", exc_info=True)

        # Handle unexpected errors during AI processing
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "reset_time": _safe_get_reset_time(usage_service),
            },
        ) from e


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
    """AI Chat利用状況を取得 - 軽量化された高速レスポンス"""
    usage_service = AIChatUsageService(session=session)

    try:
        # 軽量化: 利用統計のみを取得（制限チェックは行わない）
        stats = await usage_service.get_usage_stats(user)

        # レスポンスモデルに必要なフィールドを含める
        return AIChatUsageResponse(
            remaining_count=stats["remaining_count"],
            daily_limit=stats["daily_limit"],
            current_usage=stats["current_usage"],
            plan_name=stats["plan_name"],
            reset_time=stats["reset_time"],
            can_use_chat=stats["can_use_chat"],
        )

    except Exception as e:
        logger.error(f"Error getting AI chat usage for user {user.id}: {e}", exc_info=True)

        # Clerk API エラーの場合は専用のエラーハンドリング
        if "clerk" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "プラン情報の取得に失敗しました。しばらく後にお試しください。",
                    "error_code": "CLERK_API_ERROR",
                    "remaining_count": 0,
                    "daily_limit": 0,
                    "plan_name": "free",
                    "reset_time": usage_service._get_reset_time(),
                    "can_use_chat": False,
                },
            ) from e

        # その他のシステムエラー
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "daily_limit": 0,
                "plan_name": "free",
                "reset_time": usage_service._get_reset_time(),
                "can_use_chat": False,
            },
        ) from e


@router.post("/usage/increment", response_model=AIChatUsageResponse)
async def increment_ai_chat_usage_endpoint(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AI Chat利用回数を記録（内部API） - 高速処理最適化"""
    usage_service = AIChatUsageService(session=session)

    try:
        # 利用制限チェックと利用数インクリメントを実行
        updated_stats = await usage_service.increment_usage(user)

        # レスポンスモデルに必要なフィールドを含める
        return AIChatUsageResponse(
            remaining_count=updated_stats["remaining_count"],
            daily_limit=updated_stats["daily_limit"],
            current_usage=updated_stats["current_usage"],
            plan_name=updated_stats["plan_name"],
            reset_time=updated_stats["reset_time"],
            can_use_chat=updated_stats["can_use_chat"],
        )

    except HTTPException:
        # HTTPExceptionはそのまま再発生（403, 429など）
        raise

    except Exception as e:
        logger.error(f"Error incrementing AI chat usage for user {user.id}: {e}", exc_info=True)

        # Clerk API エラーの場合
        if "clerk" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "プラン情報の取得に失敗しました。しばらく後にお試しください。",
                    "error_code": "CLERK_API_ERROR",
                    "remaining_count": 0,
                    "daily_limit": 0,
                    "plan_name": "free",
                    "reset_time": usage_service._get_reset_time(),
                    "can_use_chat": False,
                },
            ) from e

        # データベースエラーやその他のシステムエラー
        raise HTTPException(
            status_code=500,
            detail={
                "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
                "error_code": "SYSTEM_ERROR",
                "remaining_count": 0,
                "daily_limit": 0,
                "plan_name": "free",
                "reset_time": usage_service._get_reset_time(),
                "can_use_chat": False,
            },
        ) from e


@router.get("/usage/can-use", response_model=dict)
async def can_use_ai_chat_endpoint(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AI Chat利用可否の高速チェック - 軽量エンドポイント"""
    usage_service = AIChatUsageService(session=session)

    try:
        # 高速な利用可否チェック
        can_use = await usage_service.can_use_chat(user)
        user_plan = await usage_service.get_user_plan(user)
        daily_limit = usage_service.get_daily_limit(user_plan)

        return {
            "can_use_chat": can_use,
            "plan_name": user_plan,
            "daily_limit": daily_limit,
            "reset_time": usage_service._get_reset_time(),
        }

    except Exception as e:
        logger.error(f"Error checking AI chat availability for user {user.id}: {e}", exc_info=True)

        # エラー時はfreeプランとして安全にフォールバック
        return {
            "can_use_chat": False,
            "plan_name": "free",
            "daily_limit": 0,
            "reset_time": usage_service._get_reset_time(),
        }
