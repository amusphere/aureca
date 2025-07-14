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


class GenerateTasksFromEmailsResponseModel(BaseModel):
    """メールからのタスク生成レスポンスモデル"""

    success: bool
    message: str
    generated_tasks: list[GeneratedTaskModel]


class EmailReplyDraftModel(BaseModel):
    """メール返信下書きモデル"""

    subject: str
    body: str


class EmailReplyDraftResponseModel(BaseModel):
    """メール返信下書きレスポンスモデル"""

    success: bool
    message: str
    draft: EmailReplyDraftModel
