from uuid import UUID

from app.schema import SourceType
from pydantic import BaseModel


class TaskSourceModel(BaseModel):
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
    uuid: UUID | None = None
    title: str
    description: str | None = None
    completed: bool = False
    expires_at: float | None = None
    sources: list[TaskSourceModel] = []
