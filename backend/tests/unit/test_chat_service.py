"""Unit tests for ChatService."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from app.services.chat_service import ChatService


class TestChatService:
    """Unit tests for chat service functionality."""

    @pytest.fixture
    def chat_service(self, session: Session) -> ChatService:
        """Create a ChatService instance for testing."""
        return ChatService(session)

    @pytest.fixture
    async def test_thread(self, session: Session, test_user: User):
        """Create a test chat thread."""
        return await chat_thread.create(session, test_user.id, "Test Thread")

    @pytest.mark.asyncio
    async def test_get_or_create_default_thread_existing(self, chat_service: ChatService, test_user: User):
        """Test getting existing default thread."""
        # Create a thread
        existing_thread = await chat_thread.create(chat_service.session, test_user.id, "Existing Thread")

        result = await chat_service.get_or_create_default_thread(test_user.id)

        assert result.id == existing_thread.id
        assert result.title == "Existing Thread"

    @pytest.mark.asyncio
    async def test_get_or_create_default_thread_create_new(self, chat_service: ChatService, test_user: User):
        """Test creating new default thread when none exists."""
        result = await chat_service.get_or_create_default_thread(test_user.id)

        assert result.id is not None
        assert result.user_id == test_user.id
        assert result.title is None

    @pytest.mark.asyncio
    async def test_get_or_create_default_thread_returns_most_recent(self, chat_service: ChatService, test_user: User):
        """Test that the most recent thread is returned."""
        # Create multiple threads
        await chat_thread.create(chat_service.session, test_user.id, "Thread 1")
        time.sleep(0.01)
        await chat_thread.create(chat_service.session, test_user.id, "Thread 2")
        time.sleep(0.01)
        thread3 = await chat_thread.create(chat_service.session, test_user.id, "Thread 3")

        result = await chat_service.get_or_create_default_thread(test_user.id)

        # Should return the most recent (thread3)
        assert result.id == thread3.id

    @pytest.mark.asyncio
    @patch("app.services.chat_service.AIHub")
    @patch("app.services.chat_service.llm_chat_completions")
    async def test_send_message_with_ai_response_success(
        self, mock_llm, mock_ai_hub_class, chat_service: ChatService, test_thread, test_user: User
    ):
        """Test successful message sending with AI response."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response to your message"
        mock_ai_hub_class.return_value = mock_ai_hub

        user_message = "Hello, how are you?"

        user_msg, ai_msg = await chat_service.send_message_with_ai_response(
            str(test_thread.uuid), user_message, test_user
        )

        # Verify user message
        assert user_msg.thread_id == test_thread.id
        assert user_msg.role == "user"
        assert user_msg.content == user_message

        # Verify AI message
        assert ai_msg.thread_id == test_thread.id
        assert ai_msg.role == "assistant"
        assert ai_msg.content == "AI response to your message"

        # Verify AI Hub was called correctly
        mock_ai_hub.process_chat_message.assert_called_once()
        call_args = mock_ai_hub.process_chat_message.call_args
        assert call_args[0][0] == user_message  # message
        assert call_args[0][1] == test_user  # user
        assert isinstance(call_args[0][2], list)  # history

    @pytest.mark.asyncio
    async def test_send_message_with_ai_response_thread_not_found(self, chat_service: ChatService, test_user: User):
        """Test sending message to non-existent thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.send_message_with_ai_response(fake_uuid, "Hello", test_user)

        assert exc_info.value.status_code == 404
        assert "Chat thread not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_message_with_ai_response_wrong_user(
        self, chat_service: ChatService, test_thread, test_user: User
    ):
        """Test sending message to thread owned by different user."""
        # Create another user
        other_user = User(
            id=999,
            clerk_user_id="other_user_123",
            clerk_sub="other_user_123",
            email="other@example.com",
            created_at=time.time(),
            updated_at=time.time(),
        )
        chat_service.session.add(other_user)
        chat_service.session.commit()
        chat_service.session.refresh(other_user)

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.send_message_with_ai_response(str(test_thread.uuid), "Hello", other_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.chat_service.AIHub")
    @patch("app.services.chat_service.llm_chat_completions")
    async def test_send_message_with_ai_response_ai_failure_fallback(
        self, mock_llm, mock_ai_hub_class, chat_service: ChatService, test_thread, test_user: User
    ):
        """Test AI failure with fallback response."""
        # Mock AI Hub to fail
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = Exception("AI Hub failed")
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock fallback LLM response
        mock_llm.return_value = "Fallback AI response"

        user_message = "Hello"

        user_msg, ai_msg = await chat_service.send_message_with_ai_response(
            str(test_thread.uuid), user_message, test_user
        )

        # Should get fallback response
        assert ai_msg.content == "Fallback AI response"

        # Verify fallback was called
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.AIHub")
    async def test_send_message_with_ai_response_complete_failure(
        self, mock_ai_hub_class, chat_service: ChatService, test_thread, test_user: User
    ):
        """Test complete AI failure with error message."""
        # Mock AI Hub to fail
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = Exception("AI Hub failed")
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock LLM to also fail
        with patch("app.services.chat_service.llm_chat_completions", side_effect=Exception("LLM failed")):
            user_message = "Hello"

            user_msg, ai_msg = await chat_service.send_message_with_ai_response(
                str(test_thread.uuid), user_message, test_user
            )

            # Should get error message
            assert "technical difficulties" in ai_msg.content.lower()

    @pytest.mark.asyncio
    async def test_get_conversation_context(self, chat_service: ChatService, test_thread):
        """Test getting conversation context."""
        # Create some messages
        await chat_message.create(chat_service.session, test_thread.id, "user", "Hello")
        await chat_message.create(chat_service.session, test_thread.id, "assistant", "Hi there!")
        await chat_message.create(chat_service.session, test_thread.id, "user", "How are you?")

        context = await chat_service.get_conversation_context(test_thread.id)

        assert len(context) == 3
        assert context[0] == {"role": "user", "content": "Hello"}
        assert context[1] == {"role": "assistant", "content": "Hi there!"}
        assert context[2] == {"role": "user", "content": "How are you?"}

    @pytest.mark.asyncio
    async def test_get_conversation_context_with_limit(self, chat_service: ChatService, test_thread):
        """Test getting conversation context with limit."""
        # Create 5 messages
        for i in range(5):
            role = "user" if i % 2 == 0 else "assistant"
            await chat_message.create(chat_service.session, test_thread.id, role, f"Message {i + 1}")

        context = await chat_service.get_conversation_context(test_thread.id, limit=3)

        assert len(context) == 3
        # Should get the 3 most recent messages
        assert context[0]["content"] == "Message 3"
        assert context[1]["content"] == "Message 4"
        assert context[2]["content"] == "Message 5"

    @pytest.mark.asyncio
    async def test_get_conversation_context_empty(self, chat_service: ChatService, test_thread):
        """Test getting conversation context from empty thread."""
        context = await chat_service.get_conversation_context(test_thread.id)

        assert context == []

    @pytest.mark.asyncio
    @patch("app.services.chat_service.llm_chat_completions")
    async def test_generate_thread_title_success(self, mock_llm, chat_service: ChatService, test_thread):
        """Test successful thread title generation."""
        # Create a user message
        await chat_message.create(chat_service.session, test_thread.id, "user", "How do I learn Python programming?")

        # Mock LLM response
        mock_llm.return_value = "Learning Python Programming"

        title = await chat_service.generate_thread_title(test_thread.id)

        assert title == "Learning Python Programming"

        # Verify thread was updated
        updated_thread = await chat_thread.get_by_id(chat_service.session, test_thread.id)
        assert updated_thread.title == "Learning Python Programming"

    @pytest.mark.asyncio
    async def test_generate_thread_title_no_user_messages(self, chat_service: ChatService, test_thread):
        """Test title generation with no user messages."""
        # Create only assistant messages
        await chat_message.create(chat_service.session, test_thread.id, "assistant", "Hello!")

        title = await chat_service.generate_thread_title(test_thread.id)

        assert title is None

    @pytest.mark.asyncio
    async def test_generate_thread_title_empty_thread(self, chat_service: ChatService, test_thread):
        """Test title generation with empty thread."""
        title = await chat_service.generate_thread_title(test_thread.id)

        assert title is None

    @pytest.mark.asyncio
    @patch("app.services.chat_service.llm_chat_completions")
    async def test_generate_thread_title_llm_failure(self, mock_llm, chat_service: ChatService, test_thread):
        """Test title generation when LLM fails."""
        # Create a user message
        await chat_message.create(chat_service.session, test_thread.id, "user", "How do I learn Python?")

        # Mock LLM to fail
        mock_llm.side_effect = Exception("LLM failed")

        title = await chat_service.generate_thread_title(test_thread.id)

        assert title is None

    @pytest.mark.asyncio
    @patch("app.services.chat_service.llm_chat_completions")
    async def test_generate_thread_title_long_title_truncation(self, mock_llm, chat_service: ChatService, test_thread):
        """Test title truncation for long titles."""
        # Create a user message
        await chat_message.create(chat_service.session, test_thread.id, "user", "Question about programming")

        # Mock very long title
        long_title = "This is a very long title that exceeds the maximum length limit of 50 characters"
        mock_llm.return_value = long_title

        title = await chat_service.generate_thread_title(test_thread.id)

        assert len(title) <= 50
        assert title.endswith("...")

    @pytest.mark.asyncio
    async def test_get_thread_with_messages_success(self, chat_service: ChatService, test_thread, test_user: User):
        """Test getting thread with messages."""
        # Create some messages
        await chat_message.create(chat_service.session, test_thread.id, "user", "Message 1")
        await chat_message.create(chat_service.session, test_thread.id, "assistant", "Response 1")
        await chat_message.create(chat_service.session, test_thread.id, "user", "Message 2")

        thread, messages, total_count = await chat_service.get_thread_with_messages(
            str(test_thread.uuid), test_user.id, page=1, per_page=10
        )

        assert thread.id == test_thread.id
        assert len(messages) == 3
        assert total_count == 3
        assert messages[0].content == "Message 1"
        assert messages[1].content == "Response 1"
        assert messages[2].content == "Message 2"

    @pytest.mark.asyncio
    async def test_get_thread_with_messages_not_found(self, chat_service: ChatService, test_user: User):
        """Test getting non-existent thread with messages."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.get_thread_with_messages(fake_uuid, test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_thread_with_messages_wrong_user(self, chat_service: ChatService, test_thread, test_user: User):
        """Test getting thread with messages for wrong user."""
        # Create another user
        other_user = User(
            id=999,
            clerk_user_id="other_user_123",
            clerk_sub="other_user_123",
            email="other@example.com",
            created_at=time.time(),
            updated_at=time.time(),
        )
        chat_service.session.add(other_user)
        chat_service.session.commit()
        chat_service.session.refresh(other_user)

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.get_thread_with_messages(str(test_thread.uuid), other_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_thread_success(self, chat_service: ChatService, test_thread, test_user: User):
        """Test successful thread deletion."""
        result = await chat_service.delete_thread(str(test_thread.uuid), test_user.id)

        assert result is True

        # Verify thread is deleted
        deleted_thread = await chat_thread.get_by_id(chat_service.session, test_thread.id)
        assert deleted_thread is None

    @pytest.mark.asyncio
    async def test_delete_thread_not_found(self, chat_service: ChatService, test_user: User):
        """Test deleting non-existent thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.delete_thread(fake_uuid, test_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_thread_wrong_user(self, chat_service: ChatService, test_thread, test_user: User):
        """Test deleting thread with wrong user."""
        # Create another user
        other_user = User(
            id=999,
            clerk_user_id="other_user_123",
            clerk_sub="other_user_123",
            email="other@example.com",
            created_at=time.time(),
            updated_at=time.time(),
        )
        chat_service.session.add(other_user)
        chat_service.session.commit()
        chat_service.session.refresh(other_user)

        with pytest.raises(HTTPException) as exc_info:
            await chat_service.delete_thread(str(test_thread.uuid), other_user.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_thread_success(self, chat_service: ChatService, test_user: User):
        """Test successful thread creation."""
        title = "New Chat Thread"

        thread = await chat_service.create_thread(test_user.id, title)

        assert thread.id is not None
        assert thread.user_id == test_user.id
        assert thread.title == title

    @pytest.mark.asyncio
    async def test_create_thread_without_title(self, chat_service: ChatService, test_user: User):
        """Test creating thread without title."""
        thread = await chat_service.create_thread(test_user.id)

        assert thread.id is not None
        assert thread.user_id == test_user.id
        assert thread.title is None

    @pytest.mark.asyncio
    async def test_get_user_threads_success(self, chat_service: ChatService, test_user: User):
        """Test getting user threads."""
        # Create multiple threads
        thread1 = await chat_thread.create(chat_service.session, test_user.id, "Thread 1")
        time.sleep(0.01)
        thread2 = await chat_thread.create(chat_service.session, test_user.id, "Thread 2")
        time.sleep(0.01)
        thread3 = await chat_thread.create(chat_service.session, test_user.id, "Thread 3")

        threads, total_count = await chat_service.get_user_threads(test_user.id, page=1, per_page=10)

        assert len(threads) == 3
        assert total_count == 3
        # Should be ordered by updated_at desc (most recent first)
        assert threads[0].id == thread3.id
        assert threads[1].id == thread2.id
        assert threads[2].id == thread1.id

    @pytest.mark.asyncio
    async def test_get_user_threads_pagination(self, chat_service: ChatService, test_user: User):
        """Test user threads pagination."""
        # Create 5 threads
        for i in range(5):
            await chat_thread.create(chat_service.session, test_user.id, f"Thread {i + 1}")
            time.sleep(0.01)

        # Get first page
        threads, total_count = await chat_service.get_user_threads(test_user.id, page=1, per_page=3)

        assert len(threads) == 3
        assert total_count == 5

        # Get second page
        threads, total_count = await chat_service.get_user_threads(test_user.id, page=2, per_page=3)

        assert len(threads) == 2
        assert total_count == 5

    @pytest.mark.asyncio
    async def test_get_user_threads_empty(self, chat_service: ChatService, test_user: User):
        """Test getting threads for user with no threads."""
        threads, total_count = await chat_service.get_user_threads(test_user.id)

        assert len(threads) == 0
        assert total_count == 0

    @pytest.mark.asyncio
    @patch("app.services.chat_service.AIHub")
    async def test_auto_title_generation_on_first_message(
        self, mock_ai_hub_class, chat_service: ChatService, test_user: User
    ):
        """Test automatic title generation on first message exchange."""
        # Create a thread without a title
        thread = await chat_service.create_thread(test_user.id, title=None)

        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response"
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock title generation
        with patch.object(chat_service, "generate_thread_title", return_value="Generated Title") as mock_gen_title:
            user_message = "How do I learn Python programming effectively?"

            await chat_service.send_message_with_ai_response(str(thread.uuid), user_message, test_user)

            # Should attempt title generation for substantial first message
            mock_gen_title.assert_called_once_with(thread.id)

    @pytest.mark.asyncio
    @patch("app.services.chat_service.AIHub")
    async def test_no_title_generation_for_short_message(
        self, mock_ai_hub_class, chat_service: ChatService, test_thread, test_user: User
    ):
        """Test no title generation for short messages."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response"
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock title generation
        with patch.object(chat_service, "generate_thread_title") as mock_gen_title:
            user_message = "Hi"  # Short message

            await chat_service.send_message_with_ai_response(str(test_thread.uuid), user_message, test_user)

            # Should not attempt title generation for short message
            mock_gen_title.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_isolation_in_service_methods(self, chat_service: ChatService, test_user: User):
        """Test that service methods properly isolate users."""
        # Create another user
        other_user = User(
            id=999,
            clerk_user_id="other_user_123",
            clerk_sub="other_user_123",
            email="other@example.com",
            created_at=time.time(),
            updated_at=time.time(),
        )
        chat_service.session.add(other_user)
        chat_service.session.commit()
        chat_service.session.refresh(other_user)

        # Create threads for both users
        user1_thread = await chat_service.create_thread(test_user.id, "User 1 Thread")
        user2_thread = await chat_service.create_thread(other_user.id, "User 2 Thread")

        # Test thread isolation
        user1_threads, _ = await chat_service.get_user_threads(test_user.id)
        user2_threads, _ = await chat_service.get_user_threads(other_user.id)

        assert len(user1_threads) == 1
        assert len(user2_threads) == 1
        assert user1_threads[0].id == user1_thread.id
        assert user2_threads[0].id == user2_thread.id
