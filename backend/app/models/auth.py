from typing import Any

from pydantic import BaseModel, model_validator


class UserSignInModel(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str

    @model_validator(mode="before")
    @classmethod
    def email_from_username(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if "username" in data:
            data["email"] = data["username"]
        return data


class UserCreateModel(BaseModel):
    username: str
    email: str
    password: str


class UserTokenModel(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
