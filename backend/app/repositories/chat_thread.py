from uuid import UUID

from sqlmodel import Session, select

from app.schema import ChatThread


async def find_by_user_id(session: Session, user_id: int) -> list[ChatThread]:
    """Find all chat threads for a specific user, ordered by most recent first"""
    # This query will use idx_chat_threads_user_updated_desc for optimal performance
    stmt = select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.updated_at.desc())

    return session.exec(stmt).all()


async def find_by_uuid(session: Session, uuid: str | UUID, user_id: int) -> ChatThread | None:
    """Find a chat thread by UUID with user permission check"""
    # Convert string to UUID if needed
    if isinstance(uuid, str):
        uuid = UUID(uuid)

    stmt = select(ChatThread).where(ChatThread.uuid == uuid, ChatThread.user_id == user_id)

    return session.exec(stmt).first()


async def get_by_id(session: Session, id: int) -> ChatThread | None:
    """Get a chat thread by ID"""
    return session.get(ChatThread, id)


async def create(session: Session, user_id: int, title: str | None = None) -> ChatThread:
    """Create a new chat thread"""
    import time

    now = time.time()
    thread = ChatThread(user_id=user_id, title=title, created_at=now, updated_at=now)

    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


async def update_title(session: Session, thread_id: int, title: str) -> ChatThread | None:
    """Update the title of a chat thread"""
    import time

    thread = await get_by_id(session, thread_id)
    if not thread:
        return None

    thread.title = title
    thread.updated_at = time.time()

    session.commit()
    session.refresh(thread)
    return thread


async def update_timestamp(session: Session, thread_id: int) -> ChatThread | None:
    """Update the updated_at timestamp of a chat thread (called when new messages are added)"""
    import time

    thread = await get_by_id(session, thread_id)
    if not thread:
        return None

    thread.updated_at = time.time()

    session.commit()
    session.refresh(thread)
    return thread


async def delete_by_uuid(session: Session, uuid: str | UUID, user_id: int) -> bool:
    """Delete a chat thread by UUID with user permission check (hard delete)"""
    # Convert string to UUID if needed
    if isinstance(uuid, str):
        uuid = UUID(uuid)

    thread = await find_by_uuid(session, uuid, user_id)
    if not thread:
        return False

    session.delete(thread)
    session.commit()
    return True


async def count_by_user_id(session: Session, user_id: int) -> int:
    """Count total chat threads for a user"""
    from sqlalchemy import func

    stmt = select(func.count(ChatThread.id)).where(ChatThread.user_id == user_id)
    return session.exec(stmt).one()


async def find_by_user_id_paginated(
    session: Session, user_id: int, page: int = 1, per_page: int = 30
) -> tuple[list[ChatThread], int]:
    """Find chat threads for a user with pagination"""
    from sqlalchemy import func

    # Get total count
    count_stmt = select(func.count(ChatThread.id)).where(ChatThread.user_id == user_id)
    total_count = session.exec(count_stmt).one()

    # Get paginated results
    offset = (page - 1) * per_page
    stmt = (
        select(ChatThread)
        .where(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    threads = session.exec(stmt).all()

    return threads, total_count
