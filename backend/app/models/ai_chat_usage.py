from typing import Literal

from pydantic import BaseModel, Field


class AIChatUsageResponse(BaseModel):
    """AI Chat利用状況レスポンスモデル - 2プラン対応"""

    remaining_count: int = Field(..., ge=0, description="残り利用可能回数")
    daily_limit: int = Field(..., ge=0, description="1日の利用上限回数")
    current_usage: int = Field(..., ge=0, description="本日の利用回数")
    plan_name: str = Field(..., description="ユーザーのプラン名 (free/standard)")
    reset_time: str = Field(..., description="リセット時刻 (ISO 8601形式)")
    can_use_chat: bool = Field(..., description="チャット利用可能フラグ")


class AIChatUsageError(BaseModel):
    """AI Chat利用制限エラーモデル - 詳細エラー情報付き"""

    error: str = Field(..., description="エラーメッセージ")
    error_code: Literal["USAGE_LIMIT_EXCEEDED", "PLAN_RESTRICTION", "CLERK_API_ERROR", "SYSTEM_ERROR"] = Field(
        ..., description="エラーコード"
    )
    remaining_count: int = Field(..., ge=0, description="残り利用可能回数")
    daily_limit: int = Field(..., ge=0, description="1日の利用上限回数")
    plan_name: str = Field(..., description="ユーザーのプラン名")
    reset_time: str = Field(..., description="リセット時刻 (ISO 8601形式)")
    http_status: int = Field(..., description="HTTPステータスコード")


class ClerkAPIError(BaseModel):
    """Clerk API エラー専用モデル"""

    error: str = Field(
        default="プラン情報の取得に失敗しました。しばらく後にお試しください。", description="Clerk APIエラーメッセージ"
    )
    error_code: Literal["CLERK_API_ERROR"] = Field(default="CLERK_API_ERROR", description="Clerk APIエラーコード")
    fallback_plan: str = Field(default="free", description="フォールバック時のプラン名")
    retry_after: int = Field(default=60, description="リトライ推奨時間（秒）")


class PlanLimitInfo(BaseModel):
    """プラン制限情報モデル"""

    plan_name: str = Field(..., description="プラン名")
    daily_limit: int = Field(..., ge=0, description="1日の利用上限回数")
    is_premium: bool = Field(..., description="有料プランフラグ")
    features: list[str] = Field(default_factory=list, description="プラン機能一覧")
