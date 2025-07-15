"""
Custom exception classes for AI assistant
"""


class AIAssistantError(Exception):
    """Base exception class for AI assistant"""

    pass


class PromptAnalysisError(AIAssistantError):
    """Prompt analysis error"""

    pass


class ActionExecutionError(AIAssistantError):
    """Action execution error"""

    pass


class AuthenticationError(AIAssistantError):
    """Authentication error"""

    pass


class InvalidParameterError(AIAssistantError):
    """Invalid parameter error"""

    pass


class ExternalServiceError(AIAssistantError):
    """External service (Google Calendar, etc.) error"""

    def __init__(self, message: str, service_name: str, status_code: int = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code


class RateLimitError(AIAssistantError):
    """Rate limit error"""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
