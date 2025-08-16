from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateChatThreadRequest(BaseModel):
    """Request model for creating a new chat thread"""

    title: str | None = Field(default=None, max_length=200, description="Optional thread title")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class SendMessageRequest(BaseModel):
    """Request model for sending a message to a chat thread"""

    content: str = Field(min_length=1, max_length=4000, description="Message content")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty or whitespace only")
        return v


class ChatThreadResponse(BaseModel):
    """Response model for chat thread information"""

    model_config = {"from_attributes": True}

    uuid: str
    title: str | None
    created_at: float
    updated_at: float
    message_count: int


class ChatMessageResponse(BaseModel):
    """Response model for chat message information"""

    model_config = {"from_attributes": True}

    uuid: str
    role: str = Field(description="Message role (user, assistant, system)")
    content: str
    created_at: float

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = {"user", "assistant", "system"}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class PaginationInfo(BaseModel):
    """Pagination information for paginated responses"""

    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_messages: int = Field(ge=0, description="Total number of messages")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class ChatThreadWithMessagesResponse(BaseModel):
    """Response model for chat thread with messages and pagination"""

    thread: ChatThreadResponse
    messages: list[ChatMessageResponse]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str = Field(description="Error message")
    error_code: str = Field(description="Error code for programmatic handling")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
