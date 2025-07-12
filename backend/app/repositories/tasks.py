from app.schema import Tasks
from sqlmodel import Session, select


def find_tasks(
    session: Session,
    user_id: int,
    completed: bool = False,
    expires_at: float | None = None,
) -> list[Tasks]:
    """Find all task lists for a specific user"""
    stmt = select(Tasks).where(
        Tasks.user_id == user_id,
        Tasks.completed == completed,
    ).order_by(Tasks.expires_at)

    if expires_at is not None:
        stmt = stmt.where(Tasks.expires_at >= expires_at)

    return session.exec(stmt).all()


def get_task_by_id(
    session: Session,
    id: int,
) -> Tasks | None:
    """Get a task by ID"""
    return session.get(Tasks, id)


def create_task(
    session: Session,
    user_id: int,
    title: str,
    description: str | None = None,
    expires_at: float | None = None,
) -> Tasks:
    """Create a new task"""
    task = Tasks(
        user_id=user_id,
        title=title,
        description=description,
        expires_at=expires_at,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(
    session: Session,
    id: int,
    title: str | None = None,
    description: str | None = None,
    expires_at: float | None = None,
    completed: bool | None = None,
) -> Tasks:
    """Update an existing task"""
    task = get_task_by_id(session, id)
    if not task:
        raise ValueError("task not found")

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if expires_at is not None:
        task.expires_at = expires_at
    if completed is not None:
        task.completed = completed

    session.commit()
    session.refresh(task)
    return task


def complete_task(
    session: Session,
    id: int,
) -> Tasks:
    """Mark a task as completed"""
    return update_task(session, id, completed=True)


def incomplete_task(
    session: Session,
    id: int,
) -> Tasks:
    """Mark a task as incomplete"""
    return update_task(session, id, completed=False)


def delete_task(
    session: Session,
    id: int,
) -> None:
    """Delete a task"""
    task = get_task_by_id(session, id)
    if not task:
        raise ValueError("task not found")

    session.delete(task)
    session.commit()
