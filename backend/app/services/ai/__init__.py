"""
AI Services - Hub-and-Spoke AI Assistant System

This module provides a simplified, maintainable hub-and-spoke architecture
for AI services that can integrate with various external services and databases.

Main Components:
- AIHub: Central controller for processing user requests
- SpokeManager: Manages spoke discovery, loading, and execution
- BaseSpoke: Base class for implementing service-specific spokes

Usage:
    from app.services.ai import AIHub

    # Initialize the AI hub
    hub = AIHub(user_id=123, session=db_session)

    # Process user request
    result = await hub.process_request("Send an email to john@example.com", current_user)
"""

from .core.hub import AIHub
from .core.models import NextAction, OperatorResponse, SpokeResponse
from .spokes.base import BaseSpoke
from .spokes.manager import SpokeManager
from .utils.exceptions import (
    ActionExecutionError,
    AIAssistantError,
    AuthenticationError,
    ExternalServiceError,
    InvalidParameterError,
    PromptAnalysisError,
    RateLimitError,
)
from .utils.logger import AIAssistantLogger

__all__ = [
    # Main classes
    "AIHub",
    "SpokeManager",
    "BaseSpoke",
    # Data models
    "NextAction",
    "OperatorResponse",
    "SpokeResponse",
    # Exceptions
    "AIAssistantError",
    "ActionExecutionError",
    "AuthenticationError",
    "ExternalServiceError",
    "InvalidParameterError",
    "PromptAnalysisError",
    "RateLimitError",
    # Utilities
    "AIAssistantLogger",
]
