from fastapi import APIRouter, Depends

from app.models.user import UserModel
from app.schema import User
from app.services.auth import auth_user

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserModel)
async def get_current_user(user: User = Depends(auth_user)):
    return user
