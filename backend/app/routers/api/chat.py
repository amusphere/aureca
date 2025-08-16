"""
Chat API router for managing AI chat history and conversations.

This router provides endpoints for:
- Chat thread management
- Message sending and retrieval
- AI conversation with history context
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.models.chat import (
    ChatMessageResponse,
    ChatThreadResponse,
    ChatThreadWithMessagesResponse,
    CreateChatThreadRequest,
    PaginationInfo,
    SendMessageRequest,
)
from app.schema import User
from app.services.auth import auth_user
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/threads", response_model=list[ChatThreadResponse])
async def get_chat_threads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> list[ChatThreadResponse]:
    """
    Get user's chat threads with pagination.

    Returns a list of chat threads ordered by most recently updated.
    """
    chat_service = ChatService(session)
    threads, total_count = await chat_service.get_user_threads(user.id, page, per_page)

    # Convert to response models
    thread_responses = []
    for thread in threads:
        # Count messages for each thread
        message_count = len(thread.messages) if hasattr(thread, "messages") and thread.messages else 0

        thread_responses.append(
            ChatThreadResponse(
                uuid=str(thread.uuid),
                title=thread.title,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=message_count,
            )
        )

    return thread_responses


@router.post("/threads", response_model=ChatThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_thread(
    request: CreateChatThreadRequest,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatThreadResponse:
    """
    Create a new chat thread.

    Optionally accepts a title, otherwise it will be auto-generated from the first message.
    """
    chat_service = ChatService(session)
    thread = await chat_service.create_thread(user.id, request.title)

    return ChatThreadResponse(
        uuid=str(thread.uuid),
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        message_count=0,
    )


@router.get("/threads/{thread_uuid}", response_model=ChatThreadWithMessagesResponse)
async def get_chat_thread(
    thread_uuid: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Messages per page"),
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatThreadWithMessagesResponse:
    """
    Get chat thread with paginated messages.

    Returns thread details and messages in chronological order (oldest first).
    """
    chat_service = ChatService(session)
    thread, messages, total_count = await chat_service.get_thread_with_messages(thread_uuid, user.id, page, per_page)

    # Convert messages to response models
    message_responses = [
        ChatMessageResponse(
            uuid=str(msg.uuid),
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1

    pagination = PaginationInfo(
        page=page,
        per_page=per_page,
        total_messages=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )

    thread_response = ChatThreadResponse(
        uuid=str(thread.uuid),
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        message_count=total_count,
    )

    return ChatThreadWithMessagesResponse(
        thread=thread_response,
        messages=message_responses,
        pagination=pagination,
    )


@router.post("/threads/{thread_uuid}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    thread_uuid: str,
    request: SendMessageRequest,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatMessageResponse:
    """
    Send a message to a chat thread and get AI response.

    The AI will consider the conversation history when generating a response.
    """
    chat_service = ChatService(session)
    user_msg, ai_msg = await chat_service.send_message_with_ai_response(thread_uuid, request.content, user)

    # Return the AI response
    return ChatMessageResponse(
        uuid=str(ai_msg.uuid),
        role=ai_msg.role,
        content=ai_msg.content,
        created_at=ai_msg.created_at,
    )


@router.delete("/threads/{thread_uuid}", status_code=status.HTTP_200_OK)
async def delete_chat_thread(
    thread_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> dict[str, str]:
    """
    Delete a chat thread and all its messages.

    This is a hard delete operation and cannot be undone.
    """
    chat_service = ChatService(session)
    await chat_service.delete_thread(thread_uuid, user.id)

    return {"message": "Chat thread deleted successfully"}


@router.get("/threads/{thread_uuid}/context")
async def get_conversation_context(
    thread_uuid: str,
    limit: int = Query(30, ge=1, le=100, description="Maximum number of messages to include"),
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> dict[str, Any]:
    """
    Get conversation context for AI processing.

    This endpoint is primarily for internal use and debugging.
    Returns the conversation history formatted for AI context.
    """
    chat_service = ChatService(session)

    # Verify thread access
    thread, _, _ = await chat_service.get_thread_with_messages(thread_uuid, user.id, 1, 1)

    # Get conversation context
    context = await chat_service.get_conversation_context(thread.id, limit)

    return {
        "thread_uuid": thread_uuid,
        "context_messages": len(context),
        "context": context,
    }
