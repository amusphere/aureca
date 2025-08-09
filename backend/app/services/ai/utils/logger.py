"""
Logging system for AI assistant
"""

import json
import logging
from typing import Any

from ..core.models import NextAction


class AIAssistantLogger:
    """Dedicated logger for AI assistant"""

    def __init__(self, name: str = "ai_assistant"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Console handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_action_execution(self, next_action: NextAction):
        """Log action execution"""
        log_message = (
            f"Spoke: {next_action.spoke_name}, Type: {next_action.action_type}, Parameters: {next_action.parameters}, "
        )
        self.logger.info(log_message)

    def error(self, message: str):
        """General error log"""
        self.logger.error(message)

    def info(self, message: str):
        """General info log"""
        self.logger.info(message)

    def warning(self, message: str):
        """General warning log"""
        self.logger.warning(message)

    def log_error(self, error: Exception, context: dict[str, Any] = None):
        """Error log with context"""
        log_message = f"Error occurred: {type(error).__name__}: {str(error)}"

        if context:
            log_message += f", Context: {json.dumps(context, default=str)}"

        self.logger.error(log_message, exc_info=True)
