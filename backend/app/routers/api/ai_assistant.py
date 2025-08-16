import logging
import time
from datetime import UTC, datetime, timedelta

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
    """Safely get reset time, returning next midnight UTC if there's an error."""
    try:
        return usage_service._get_reset_time()
    except Exception:
        # Fallback: calculate next midnight UTC
        now = datetime.now(UTC)
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_midnight.isoformat()


@router.post("/process", response_model=AIResponseModel)
async def process_ai_request_endpoint(
    request: AIRequestModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AIアシスタントにリクエストを送信して処理結果を取得 - 新サービス層統合版

    パフォーマンス最適化:
    - 高速な利用可否チェック
    - 効率的なエラーハンドリング
    - 詳細なパフォーマンス監視
    """
    start_time = time.time()
    usage_service = AIChatUsageService(session=session)

    try:
        # Phase 1: 高速な利用可否チェック - 新しいサービス層インターフェース使用
        # 🚨 暫定対応: プランチェックを一旦オミット 🚨
        # TODO: フロントエンドでのプラン取得が安定したら復活
        check_start = time.time()
        can_use = True  # 暫定的に全ユーザーが利用可能とする
        check_duration = time.time() - check_start

        logger.debug(
            f"🚨 WORKAROUND: Usage check for user {user.id} completed in {check_duration:.3f}s: {can_use} (check omitted)"
        )

        # if not can_use:
        #     # 詳細な制限チェックでエラー情報を取得 - 改善されたエラーレスポンス
        #     await usage_service.check_usage_limit(user)

        # Phase 2: AI処理実行
        ai_start = time.time()
        hub = AIHub(user.id, session)
        result = await hub.process_request(prompt=request.prompt, current_user=user)
        ai_duration = time.time() - ai_start

        logger.debug(f"AI processing for user {user.id} completed in {ai_duration:.3f}s")

        # Phase 3: 利用数インクリメント - パフォーマンス最適化
        # 🚨 暫定対応: 利用数インクリメントを一旦オミット 🚨
        # TODO: フロントエンドでのプラン取得が安定したら復活
        increment_start = time.time()
        # await usage_service.increment_usage(user)  # 暫定的にコメントアウト
        increment_duration = time.time() - increment_start
        logger.debug(f"🚨 WORKAROUND: Usage increment for user {user.id} omitted")

        total_duration = time.time() - start_time
        logger.info(
            f"AI request completed for user {user.id} - "
            f"Total: {total_duration:.3f}s "
            f"(Check: {check_duration:.3f}s, AI: {ai_duration:.3f}s, Increment: {increment_duration:.3f}s)"
        )

        return result

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (403, 429) with enhanced error details
        total_duration = time.time() - start_time
        logger.warning(f"AI process request blocked for user {user.id} after {total_duration:.3f}s: {http_exc.detail}")
        raise
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"Error processing AI request for user {user.id} after {total_duration:.3f}s: {e}", exc_info=True)

        # Get user stats for better error context - with fallback handling
        try:
            stats_start = time.time()
            stats = await usage_service.get_usage_stats(user)
            stats_duration = time.time() - stats_start

            remaining_count = stats.get("remaining_count", 0)
            reset_time = stats.get("reset_time", _safe_get_reset_time(usage_service))
            plan_name = stats.get("plan_name", "free")
            daily_limit = stats.get("daily_limit", 0)

            logger.debug(f"Stats retrieval for error context took {stats_duration:.3f}s")
        except Exception as stats_error:
            # Fallback values if stats retrieval fails
            logger.warning(f"Failed to get stats for error context: {stats_error}")
            remaining_count = 0
            reset_time = _safe_get_reset_time(usage_service)
            plan_name = "free"
            daily_limit = 0

        # Enhanced error response with more context
        error_detail = {
            "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
            "error_code": "SYSTEM_ERROR",
            "remaining_count": remaining_count,
            "daily_limit": daily_limit,
            "plan_name": plan_name,
            "reset_time": reset_time,
            "can_use_chat": False,
        }

        # Check if it's a Clerk API related error
        if "clerk" in str(e).lower():
            error_detail.update({
                "error": "プラン情報の取得に失敗しました。しばらく後にお試しください。",
                "error_code": "CLERK_API_ERROR",
            })
            raise HTTPException(status_code=503, detail=error_detail) from e

        # General system error
        raise HTTPException(status_code=500, detail=error_detail) from e


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

    except HTTPException:
        # Propagate HTTPException such as 403 (plan) and 429 (limit)
        raise
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
                    "reset_time": _safe_get_reset_time(usage_service),
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
                "reset_time": _safe_get_reset_time(usage_service),
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
