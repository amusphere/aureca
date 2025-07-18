from app.database import get_session
from app.models.task import TaskModel
from app.repositories.tasks import (
    create_task,
    delete_task_by_uuid,
    find_tasks,
    get_task_by_uuid,
    update_task_by_uuid,
)
from app.schema import User
from app.services.auth import auth_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskModel])
async def get_tasks_endpoint(
    completed: bool = False,
    expires_at: float | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """ユーザーのタスク一覧を取得"""
    return find_tasks(
        session=session,
        user_id=user.id,
        completed=completed,
        expires_at=expires_at,
    )


@router.get("/{task_uuid}", response_model=TaskModel)
async def get_task_endpoint(
    task_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """指定したUUIDのタスクを取得"""
    task = get_task_by_uuid(session=session, uuid=task_uuid, user_id=user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.post("", response_model=TaskModel)
async def create_task_endpoint(
    task: TaskModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """新しいタスクを作成"""
    return create_task(
        session=session,
        user_id=user.id,
        title=task.title,
        description=task.description,
        expires_at=task.expires_at,
    )


@router.patch("/{task_uuid}", response_model=TaskModel)
async def update_task_endpoint(
    task_uuid: str,
    task: TaskModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを更新"""
    existing_task = get_task_by_uuid(session=session, uuid=task_uuid, user_id=user.id)
    if not existing_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return update_task_by_uuid(
        session=session,
        uuid=task_uuid,
        user_id=user.id,
        title=task.title,
        description=task.description,
        expires_at=task.expires_at,
        completed=task.completed,
    )


@router.delete("/{task_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを削除"""
    existing_task = get_task_by_uuid(session=session, uuid=task_uuid, user_id=user.id)
    if not existing_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    delete_task_by_uuid(session=session, uuid=task_uuid, user_id=user.id)
