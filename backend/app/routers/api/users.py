from app.database import get_session
from app.models.user import UserModel
from app.schema import User
from app.services.auth import auth_user, delete_current_user
from fastapi import APIRouter, Depends
from sqlmodel import Session

router = APIRouter(prefix="/users")


@router.delete("")
async def delete_current_user_endpoint(
    user: User = Depends(auth_user),
    session: Session = Depends(get_session),
):
    """Delete current user and all related data"""
    delete_current_user(user, session)
    return {"message": "User deleted successfully"}


@router.get("/me", response_model=UserModel)
async def get_current_user(user: User = Depends(auth_user)):
    return user
