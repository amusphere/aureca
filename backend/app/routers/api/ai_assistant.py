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
    thread_uuid: str | None = None,
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

        # Phase 2: AI処理実行 (with optional chat history)
        ai_start = time.time()
        hub = AIHub(user.id, session)

        # Get conversation history if thread_uuid is provided
        conversation_history = None
        if thread_uuid:
            try:
                from app.services.chat_service import ChatService

                chat_service = ChatService(session)

                # Verify thread access and get conversation context
                thread_result = await chat_service.get_thread_with_messages(thread_uuid, user.id, 1, 1)
                if thread_result:
                    thread, _, _ = thread_result
                    conversation_history = await chat_service.get_conversation_context(thread.id, limit=30)
            except Exception as e:
                logger.warning(f"Failed to get conversation history for thread {thread_uuid}: {str(e)}")
                # Continue without history if there's an error
                conversation_history = None

        result = await hub.process_request(
            prompt=request.prompt, current_user=user, conversation_history=conversation_history
        )
        ai_duration = time.time() - ai_start

        logger.debug(f"AI processing for user {user.id} completed in {ai_duration:.3f}s")

        # Phase 3: 利用数インクリメント - パフォーマンス最適化
        # 🚨 暫定対応: プラン制限チェックなしで利用回数のみインクリメント 🚨
        # TODO: フロントエンドでのプラン取得が安定したら元のincrement_usageに戻す
        increment_start = time.time()
        await usage_service.increment_usage_without_check(user)
        increment_duration = time.time() - increment_start

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
            error_detail.update(
                {
                    "error": "プラン情報の取得に失敗しました。しばらく後にお試しください。",
                    "error_code": "CLERK_API_ERROR",
                }
            )
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
        # 🚨 暫定対応: プラン制限チェックなしで利用数インクリメントのみ実行 🚨
        # TODO: フロントエンドでのプラン取得が安定したら元のincrement_usageに戻す
        updated_stats = await usage_service.increment_usage_without_check(user)

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


@router.post("/chat", response_model=dict)
async def process_ai_chat_with_history(
    request: AIRequestModel,
    thread_uuid: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """
    Process AI request with automatic chat history management.

    This endpoint:
    1. Creates or uses existing chat thread
    2. Saves user message to history
    3. Processes AI request with conversation context
    4. Saves AI response to history
    5. Returns both the AI response and thread information
    """
    start_time = time.time()
    usage_service = AIChatUsageService(session=session)

    try:
        # Phase 1: Usage check (same as regular AI process)
        check_start = time.time()
        can_use = True  # 暫定的に全ユーザーが利用可能とする
        check_duration = time.time() - check_start

        logger.debug(
            f"🚨 WORKAROUND: Usage check for user {user.id} completed in {check_duration:.3f}s: {can_use} (check omitted)"
        )

        # Phase 2: Chat history integration
        chat_start = time.time()
        from app.services.chat_service import ChatService

        chat_service = ChatService(session)

        # Get or create thread
        if thread_uuid:
            # Use existing thread
            thread_result = await chat_service.get_thread_with_messages(thread_uuid, user.id, 1, 1)
            if not thread_result:
                raise HTTPException(status_code=404, detail="Chat thread not found")
            thread, _, _ = thread_result
        else:
            # Create or get default thread
            thread = await chat_service.get_or_create_default_thread(user.id)

        # Send message and get AI response with history context
        user_msg, ai_msg = await chat_service.send_message_with_ai_response(str(thread.uuid), request.prompt, user)
        chat_duration = time.time() - chat_start

        # Phase 3: Usage increment
        increment_start = time.time()
        await usage_service.increment_usage_without_check(user)
        increment_duration = time.time() - increment_start

        total_duration = time.time() - start_time
        logger.info(
            f"AI chat request completed for user {user.id} - "
            f"Total: {total_duration:.3f}s "
            f"(Check: {check_duration:.3f}s, Chat: {chat_duration:.3f}s, Increment: {increment_duration:.3f}s)"
        )

        return {
            "success": True,
            "thread_uuid": str(thread.uuid),
            "user_message": {
                "uuid": str(user_msg.uuid),
                "content": user_msg.content,
                "created_at": user_msg.created_at,
            },
            "ai_response": {
                "uuid": str(ai_msg.uuid),
                "content": ai_msg.content,
                "created_at": ai_msg.created_at,
            },
            "thread_info": {
                "title": thread.title,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
            },
        }

    except HTTPException as http_exc:
        total_duration = time.time() - start_time
        logger.warning(f"AI chat request blocked for user {user.id} after {total_duration:.3f}s: {http_exc.detail}")
        raise
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(
            f"Error processing AI chat request for user {user.id} after {total_duration:.3f}s: {e}", exc_info=True
        )

        # Enhanced error response
        try:
            stats = await usage_service.get_usage_stats(user)
            remaining_count = stats.get("remaining_count", 0)
            reset_time = stats.get("reset_time", _safe_get_reset_time(usage_service))
            plan_name = stats.get("plan_name", "free")
            daily_limit = stats.get("daily_limit", 0)
        except Exception:
            remaining_count = 0
            reset_time = _safe_get_reset_time(usage_service)
            plan_name = "free"
            daily_limit = 0

        error_detail = {
            "error": "一時的なエラーが発生しました。しばらく後にお試しください。",
            "error_code": "SYSTEM_ERROR",
            "remaining_count": remaining_count,
            "daily_limit": daily_limit,
            "plan_name": plan_name,
            "reset_time": reset_time,
            "can_use_chat": False,
        }

        if "clerk" in str(e).lower():
            error_detail.update(
                {
                    "error": "プラン情報の取得に失敗しました。しばらく後にお試しください。",
                    "error_code": "CLERK_API_ERROR",
                }
            )
            raise HTTPException(status_code=503, detail=error_detail) from e

        raise HTTPException(status_code=500, detail=error_detail) from e
