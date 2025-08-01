from uuid import UUID

from app.schema import SourceType, TaskPriority
from pydantic import BaseModel


class TaskSourceModel(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID | None = None
    source_type: SourceType
    source_url: str | None = None
    source_id: str | None = None
    title: str | None = None
    content: str | None = None
    extra_data: str | None = None
    created_at: float | None = None
    updated_at: float | None = None


class TaskModel(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID | None = None
    title: str
    description: str | None = None
    completed: bool = False
    expires_at: float | None = None
    priority: TaskPriority | None = None
    created_at: float | None = None
    updated_at: float | None = None
    sources: list[TaskSourceModel] = []


class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    expires_at: float | None = None
    priority: TaskPriority | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    expires_at: float | None = None
    completed: bool | None = None
    priority: TaskPriority | None = None
