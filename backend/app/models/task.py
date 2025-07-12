from uuid import UUID

from pydantic import BaseModel


class TaskModel(BaseModel):
    uuid: UUID | None = None
    title: str
    description: str | None = None
    completed: bool
    expires_at: float | None = None
