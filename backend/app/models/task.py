from pydantic import BaseModel


class TaskModel(BaseModel):
    uuid: str | None = None
    title: str
    description: str | None = None
    completed: bool
    expires_at: float | None = None
