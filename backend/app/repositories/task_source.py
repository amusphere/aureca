from uuid import UUID

from sqlmodel import Session, select

from app.schema import TaskSource


def get_task_source_by_uuid(
    session: Session,
    uuid: str | UUID,
) -> TaskSource | None:
    """Get a task source by UUID"""
    try:
        if isinstance(uuid, str):
            uuid_obj = UUID(uuid)
        else:
            uuid_obj = uuid
    except ValueError:
        return None

    stmt = select(TaskSource).where(TaskSource.uuid == uuid_obj)
    return session.exec(stmt).first()


def get_task_sources_by_task_id(session: Session, task_id: int) -> list[TaskSource]:
    """タスクIDでTaskSourceリストを取得"""
    statement = select(TaskSource).where(TaskSource.task_id == task_id)
    return list(session.exec(statement).all())


def create_task_source(
    session: Session,
    task_id: int,
    source_type: str,
    source_url: str | None = None,
    source_id: str | None = None,
    title: str | None = None,
    content: str | None = None,
    extra_data: str | None = None,
) -> TaskSource:
    """Create a new task source"""
    task_source = TaskSource(
        task_id=task_id,
        source_type=source_type,
        source_url=source_url,
        source_id=source_id,
        title=title,
        content=content,
        extra_data=extra_data,
    )
    session.add(task_source)
    session.commit()
    session.refresh(task_source)
    return task_source


def update_task_source(
    session: Session,
    uuid: str | UUID,
    source_url: str | None = None,
    source_id: str | None = None,
    title: str | None = None,
    content: str | None = None,
    extra_data: str | None = None,
) -> TaskSource | None:
    """Update an existing task source"""
    task_source = get_task_source_by_uuid(session, uuid)
    if not task_source:
        return None

    if source_url is not None:
        task_source.source_url = source_url
    if source_id is not None:
        task_source.source_id = source_id
    if title is not None:
        task_source.title = title
    if content is not None:
        task_source.content = content
    if extra_data is not None:
        task_source.extra_data = extra_data

    session.commit()
    session.refresh(task_source)
    return task_source


def delete_task_source(
    session: Session,
    uuid: str | UUID,
) -> None:
    """Delete a task source"""
    task_source = get_task_source_by_uuid(session, uuid)
    if not task_source:
        raise ValueError("task source not found")

    session.delete(task_source)
    session.commit()


def find_task_sources_by_task_id(
    session: Session,
    task_id: int,
) -> list[TaskSource]:
    """Find all task sources for a specific task"""
    stmt = select(TaskSource).where(TaskSource.task_id == task_id)
    return list(session.exec(stmt).all())


def find_task_sources_by_source_type(
    session: Session,
    source_type: str,
) -> list[TaskSource]:
    """Find all task sources by source type"""
    stmt = select(TaskSource).where(TaskSource.source_type == source_type)
    return list(session.exec(stmt).all())


def get_task_source_by_source_id(
    session: Session,
    source_id: str,
    source_type: str | None = None,
) -> TaskSource | None:
    """Get a task source by source_id and optionally source_type"""
    stmt = select(TaskSource).where(TaskSource.source_id == source_id)
    if source_type:
        stmt = stmt.where(TaskSource.source_type == source_type)
    return session.exec(stmt).first()
