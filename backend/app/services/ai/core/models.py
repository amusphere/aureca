"""
Core data models for AI services
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NextAction(BaseModel):
    """Next action to be executed"""

    model_config = ConfigDict(extra="forbid")

    spoke_name: str  # Spoke name
    action_type: str  # Spoke action type
    parameters: str = Field(default="{}")  # Action parameters (JSON string)
    priority: int = Field(default=1, ge=1)  # 1 is highest priority
    description: str  # Action description

    @field_validator("parameters", mode="before")
    @classmethod
    def validate_parameters(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v

    def get_parameters_dict(self) -> Dict[str, Any]:
        """Get parameters as dictionary"""
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}


class OperatorResponse(BaseModel):
    """Response from operator"""

    model_config = ConfigDict(extra="forbid")

    actions: List[NextAction]
    analysis: str  # Prompt analysis result description
    confidence: float = Field(ge=0.0, le=1.0)  # Confidence level (0.0-1.0)


class SpokeResponse(BaseModel):
    """Response from spoke"""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
