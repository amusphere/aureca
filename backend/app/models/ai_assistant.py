from uuid import UUID

from pydantic import BaseModel


class AIRequestModel(BaseModel):
    """AIリクエストモデル"""

    prompt: str


class AIResponseModel(BaseModel):
    """AIレスポンスモデル"""

    success: bool
    operator_response: dict | None = None
    execution_results: list = []
    summary: dict
    error: str | None = None


class GeneratedTaskModel(BaseModel):
    """生成されたタスクモデル"""

    uuid: UUID
    title: str
    description: str | None = None
    completed: bool = False
    expires_at: float | None = None


class GeneratedTasksBySourceModel(BaseModel):
    """サービス別生成タスクモデル"""

    Gmail: list[GeneratedTaskModel] = []
    GoogleCalendar: list[GeneratedTaskModel] = []
