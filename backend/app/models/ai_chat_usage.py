from pydantic import BaseModel


class AIChatUsageResponse(BaseModel):
    """AI Chat利用状況レスポンスモデル"""

    remaining_count: int
    daily_limit: int
    reset_time: str  # ISO 8601形式
    can_use_chat: bool


class AIChatUsageError(BaseModel):
    """AI Chat利用制限エラーモデル"""

    error: str
    error_code: str
    remaining_count: int
    reset_time: str
