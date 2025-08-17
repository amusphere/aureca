from uuid import UUID

from sqlmodel import Session, select

from app.schema import ChatMessage


async def find_by_thread_id_paginated(
    session: Session, thread_id: int, page: int = 1, per_page: int = 30
) -> tuple[list[ChatMessage], int]:
    """Find messages for a thread with pagination, ordered chronologically (oldest first)"""
    from sqlalchemy import func

    # Get total count
    count_stmt = select(func.count(ChatMessage.id)).where(ChatMessage.thread_id == thread_id)
    total_count = session.exec(count_stmt).one()

    # Get paginated results - oldest first for chat display
    offset = (page - 1) * per_page
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(per_page)
    )

    messages = session.exec(stmt).all()

    return messages, total_count


async def get_recent_messages_for_context(session: Session, thread_id: int, limit: int = 30) -> list[ChatMessage]:
    """Get the most recent messages for AI context, ordered chronologically (oldest first)"""
    # This query will use idx_chat_messages_thread_created_desc for optimal performance
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )

    # Get messages in reverse order (newest first), then reverse to get chronological order
    messages = session.exec(stmt).all()
    return list(reversed(messages))


async def find_by_thread_id(session: Session, thread_id: int) -> list[ChatMessage]:
    """Find all messages for a thread, ordered chronologically (oldest first)"""
    stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc())

    return session.exec(stmt).all()


async def get_by_id(session: Session, id: int) -> ChatMessage | None:
    """Get a message by ID"""
    return session.get(ChatMessage, id)


async def get_by_uuid(session: Session, uuid: str | UUID) -> ChatMessage | None:
    """Get a message by UUID"""
    # Convert string to UUID if needed
    if isinstance(uuid, str):
        uuid = UUID(uuid)

    stmt = select(ChatMessage).where(ChatMessage.uuid == uuid)
    return session.exec(stmt).first()


async def create(session: Session, thread_id: int, role: str, content: str) -> ChatMessage:
    """Create a new chat message"""
    import time

    message = ChatMessage(thread_id=thread_id, role=role, content=content, created_at=time.time())

    session.add(message)
    session.commit()
    session.refresh(message)
    return message


async def create_batch(session: Session, messages_data: list[dict]) -> list[ChatMessage]:
    """Create multiple messages in a single transaction"""
    import time

    messages = []
    for data in messages_data:
        message = ChatMessage(
            thread_id=data["thread_id"], role=data["role"], content=data["content"], created_at=time.time()
        )
        messages.append(message)
        session.add(message)

    session.commit()

    # Refresh all messages to get their IDs
    for message in messages:
        session.refresh(message)

    return messages


async def count_by_thread_id(session: Session, thread_id: int) -> int:
    """Count total messages in a thread"""
    from sqlalchemy import func

    stmt = select(func.count(ChatMessage.id)).where(ChatMessage.thread_id == thread_id)
    return session.exec(stmt).one()


async def get_first_message_content(session: Session, thread_id: int) -> str | None:
    """Get the content of the first user message in a thread (for auto-generating titles)"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id, ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.asc())
        .limit(1)
    )

    message = session.exec(stmt).first()
    return message.content if message else None


async def delete_by_thread_id(session: Session, thread_id: int) -> int:
    """Delete all messages in a thread (used when thread is deleted)"""
    stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id)
    messages = session.exec(stmt).all()

    count = len(messages)
    for message in messages:
        session.delete(message)

    session.commit()
    return count


async def get_conversation_history_for_ai(session: Session, thread_id: int, limit: int = 30) -> list[dict[str, str]]:
    """Get conversation history formatted for AI context (OpenAI format)"""
    messages = await get_recent_messages_for_context(session, thread_id, limit)

    # Convert to OpenAI format
    conversation = []
    for message in messages:
        conversation.append({"role": message.role, "content": message.content})

    return conversation
