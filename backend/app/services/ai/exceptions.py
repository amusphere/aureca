"""
AIアシスタント用のカスタム例外クラス
"""


class AIAssistantError(Exception):
    """AIアシスタントの基底例外クラス"""

    pass


class PromptAnalysisError(AIAssistantError):
    """プロンプト解析エラー"""

    pass


class ActionExecutionError(AIAssistantError):
    """アクション実行エラー"""

    pass


class AuthenticationError(AIAssistantError):
    """認証エラー"""

    pass


class InvalidParameterError(AIAssistantError):
    """無効なパラメータエラー"""

    pass


class ExternalServiceError(AIAssistantError):
    """外部サービス（Google Calendar等）エラー"""

    def __init__(self, message: str, service_name: str, status_code: int = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code


class RateLimitError(AIAssistantError):
    """レート制限エラー"""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
