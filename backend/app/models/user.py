from uuid import UUID

from pydantic import BaseModel


class UserModel(BaseModel):
    uuid: UUID
    email: str
    name: str | None = None
