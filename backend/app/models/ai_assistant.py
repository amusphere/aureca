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
