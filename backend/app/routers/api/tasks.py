from app.database import get_session
from app.models.task import TaskModel
from app.repositories.tasks import (
    complete_task,
    create_task,
    delete_task,
    find_tasks,
    get_task_by_id,
    incomplete_task,
    update_task,
)
from app.schema import User
from app.services.auth import auth_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[TaskModel])
async def get_tasks_endpoint(
    completed: bool = False,
    expires_at: float | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """ユーザーのタスク一覧を取得"""
    try:
        tasks = find_tasks(
            session=session,
            user_id=user.id,
            completed=completed,
            expires_at=expires_at,
        )

        return [
            TaskModel(
                uuid=str(task.uuid),
                title=task.title,
                description=task.description,
                completed=task.completed,
                expires_at=task.expires_at,
            )
            for task in tasks
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}",
        )


@router.get("/{task_id}", response_model=TaskModel)
async def get_task_endpoint(
    task_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """指定したIDのタスクを取得"""
    try:
        task = get_task_by_id(session=session, id=task_id)

        if not task or task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return TaskModel(
            uuid=str(task.uuid),
            title=task.title,
            description=task.description,
            completed=task.completed,
            expires_at=task.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}",
        )


@router.post("/", response_model=TaskModel)
async def create_task_endpoint(
    task: TaskModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """新しいタスクを作成"""
    try:
        new_task = create_task(
            session=session,
            user_id=user.id,
            title=task.title,
            description=task.description,
            expires_at=task.expires_at,
        )

        return TaskModel(
            uuid=str(new_task.uuid),
            title=new_task.title,
            description=new_task.description,
            completed=new_task.completed,
            expires_at=new_task.expires_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.patch("/{task_id}", response_model=TaskModel)
async def update_task_endpoint(
    task_id: int,
    task: TaskModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを更新"""
    try:
        # タスクが存在し、ユーザーが所有者かチェック
        existing_task = get_task_by_id(session=session, id=task_id)
        if not existing_task or existing_task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        updated_task = update_task(
            session=session,
            id=task_id,
            title=task.title,
            description=task.description,
            expires_at=task.expires_at,
            completed=task.completed,
        )

        return TaskModel(
            uuid=str(updated_task.uuid),
            title=updated_task.title,
            description=updated_task.description,
            completed=updated_task.completed,
            expires_at=updated_task.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.patch("/{task_id}/complete", response_model=TaskModel)
async def complete_task_endpoint(
    task_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを完了済みにマーク"""
    try:
        # タスクが存在し、ユーザーが所有者かチェック
        existing_task = get_task_by_id(session=session, id=task_id)
        if not existing_task or existing_task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        completed_task = complete_task(session=session, id=task_id)

        return TaskModel(
            uuid=str(completed_task.uuid),
            title=completed_task.title,
            description=completed_task.description,
            completed=completed_task.completed,
            expires_at=completed_task.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete task: {str(e)}",
        )


@router.patch("/{task_id}/incomplete", response_model=TaskModel)
async def incomplete_task_endpoint(
    task_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを未完了にマーク"""
    try:
        # タスクが存在し、ユーザーが所有者かチェック
        existing_task = get_task_by_id(session=session, id=task_id)
        if not existing_task or existing_task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        incompleted_task = incomplete_task(session=session, id=task_id)

        return TaskModel(
            uuid=str(incompleted_task.uuid),
            title=incompleted_task.title,
            description=incompleted_task.description,
            completed=incompleted_task.completed,
            expires_at=incompleted_task.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark task as incomplete: {str(e)}",
        )


@router.delete("/{task_id}")
async def delete_task_endpoint(
    task_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """タスクを削除"""
    try:
        # タスクが存在し、ユーザーが所有者かチェック
        existing_task = get_task_by_id(session=session, id=task_id)
        if not existing_task or existing_task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        delete_task(session=session, id=task_id)

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )
