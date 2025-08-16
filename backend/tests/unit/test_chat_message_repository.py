"""Unit tests for ChatMessageRepository."""

import time
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User


class TestChatMessageRepository:
    """Unit tests for chat message repository functionality."""

    @pytest.fixture
    async def test_thread(self, session: Session, test_user: User):
        """Create a test chat thread for message tests."""
        return await chat_thread.create(session, test_user.id, "Test Thread")

    @pytest.mark.asyncio
    async def test_create_message(self, session: Session, test_thread):
        """Test creating a new chat message."""
        role = "user"
        content = "Hello, this is a test message"

        message = await chat_message.create(session, test_thread.id, role, content)

        assert message.id is not None
        assert message.uuid is not None
        assert message.thread_id == test_thread.id
        assert message.role == role
        assert message.content == content
        assert message.created_at > 0

    @pytest.mark.asyncio
    async def test_create_batch_messages(self, session: Session, test_thread):
        """Test creating multiple messages in a batch."""
        messages_data = [
            {"thread_id": test_thread.id, "role": "user", "content": "First message"},
            {"thread_id": test_thread.id, "role": "assistant", "content": "Second message"},
            {"thread_id": test_thread.id, "role": "user", "content": "Third message"},
        ]

        messages = await chat_message.create_batch(session, messages_data)

        assert len(messages) == 3
        for i, message in enumerate(messages):
            assert message.id is not None
            assert message.uuid is not None
            assert message.thread_id == test_thread.id
            assert message.role == messages_data[i]["role"]
            assert message.content == messages_data[i]["content"]

    @pytest.mark.asyncio
    async def test_get_by_id(self, session: Session, test_thread):
        """Test getting a message by ID."""
        message = await chat_message.create(session, test_thread.id, "user", "Test message")

        found_message = await chat_message.get_by_id(session, message.id)

        assert found_message is not None
        assert found_message.id == message.id
        assert found_message.content == message.content

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent(self, session: Session):
        """Test getting a message by non-existent ID."""
        found_message = await chat_message.get_by_id(session, 99999)

        assert found_message is None

    @pytest.mark.asyncio
    async def test_get_by_uuid(self, session: Session, test_thread):
        """Test getting a message by UUID."""
        message = await chat_message.create(session, test_thread.id, "user", "Test message")

        found_message = await chat_message.get_by_uuid(session, str(message.uuid))

        assert found_message is not None
        assert found_message.id == message.id
        assert found_message.uuid == message.uuid

    @pytest.mark.asyncio
    async def test_get_by_uuid_with_uuid_object(self, session: Session, test_thread):
        """Test getting a message by UUID object."""
        message = await chat_message.create(session, test_thread.id, "user", "Test message")

        found_message = await chat_message.get_by_uuid(session, message.uuid)

        assert found_message is not None
        assert found_message.id == message.id

    @pytest.mark.asyncio
    async def test_get_by_uuid_nonexistent(self, session: Session):
        """Test getting a message by non-existent UUID."""
        fake_uuid = str(uuid4())

        found_message = await chat_message.get_by_uuid(session, fake_uuid)

        assert found_message is None

    @pytest.mark.asyncio
    async def test_find_by_thread_id(self, session: Session, test_thread):
        """Test finding all messages for a thread."""
        # Create messages with different timestamps
        message1 = await chat_message.create(session, test_thread.id, "user", "First message")
        time.sleep(0.01)
        message2 = await chat_message.create(session, test_thread.id, "assistant", "Second message")
        time.sleep(0.01)
        message3 = await chat_message.create(session, test_thread.id, "user", "Third message")

        messages = await chat_message.find_by_thread_id(session, test_thread.id)

        assert len(messages) == 3
        # Should be ordered chronologically (oldest first)
        assert messages[0].id == message1.id
        assert messages[1].id == message2.id
        assert messages[2].id == message3.id

    @pytest.mark.asyncio
    async def test_find_by_thread_id_empty(self, session: Session, test_thread):
        """Test finding messages for a thread with no messages."""
        messages = await chat_message.find_by_thread_id(session, test_thread.id)

        assert len(messages) == 0
        assert messages == []

    @pytest.mark.asyncio
    async def test_find_by_thread_id_paginated(self, session: Session, test_thread):
        """Test finding messages with pagination."""
        # Create 5 messages
        messages = []
        for i in range(5):
            message = await chat_message.create(session, test_thread.id, "user", f"Message {i + 1}")
            messages.append(message)
            time.sleep(0.01)  # Ensure different timestamps

        # Test first page (3 items per page)
        page1_messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, test_thread.id, page=1, per_page=3
        )

        assert len(page1_messages) == 3
        assert total_count == 5
        # Should be ordered chronologically (oldest first)
        assert page1_messages[0].content == "Message 1"
        assert page1_messages[1].content == "Message 2"
        assert page1_messages[2].content == "Message 3"

        # Test second page
        page2_messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, test_thread.id, page=2, per_page=3
        )

        assert len(page2_messages) == 2
        assert total_count == 5
        assert page2_messages[0].content == "Message 4"
        assert page2_messages[1].content == "Message 5"

    @pytest.mark.asyncio
    async def test_find_by_thread_id_paginated_empty(self, session: Session, test_thread):
        """Test pagination with no messages."""
        messages, total_count = await chat_message.find_by_thread_id_paginated(
            session, test_thread.id, page=1, per_page=10
        )

        assert len(messages) == 0
        assert total_count == 0

    @pytest.mark.asyncio
    async def test_get_recent_messages_for_context(self, session: Session, test_thread):
        """Test getting recent messages for AI context."""
        # Create 5 messages
        messages = []
        for i in range(5):
            message = await chat_message.create(session, test_thread.id, "user", f"Message {i + 1}")
            messages.append(message)
            time.sleep(0.01)  # Ensure different timestamps

        # Get recent messages (limit 3)
        recent_messages = await chat_message.get_recent_messages_for_context(session, test_thread.id, limit=3)

        assert len(recent_messages) == 3
        # Should be in chronological order (oldest first) but only the 3 most recent
        assert recent_messages[0].content == "Message 3"
        assert recent_messages[1].content == "Message 4"
        assert recent_messages[2].content == "Message 5"

    @pytest.mark.asyncio
    async def test_get_recent_messages_for_context_less_than_limit(self, session: Session, test_thread):
        """Test getting recent messages when there are fewer than the limit."""
        # Create 2 messages
        await chat_message.create(session, test_thread.id, "user", "Message 1")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "assistant", "Message 2")

        # Request 5 messages but only 2 exist
        recent_messages = await chat_message.get_recent_messages_for_context(session, test_thread.id, limit=5)

        assert len(recent_messages) == 2
        assert recent_messages[0].content == "Message 1"
        assert recent_messages[1].content == "Message 2"

    @pytest.mark.asyncio
    async def test_count_by_thread_id(self, session: Session, test_thread):
        """Test counting messages in a thread."""
        # Initially no messages
        count = await chat_message.count_by_thread_id(session, test_thread.id)
        assert count == 0

        # Create some messages
        await chat_message.create(session, test_thread.id, "user", "Message 1")
        await chat_message.create(session, test_thread.id, "assistant", "Message 2")
        await chat_message.create(session, test_thread.id, "user", "Message 3")

        count = await chat_message.count_by_thread_id(session, test_thread.id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_first_message_content(self, session: Session, test_thread):
        """Test getting the first user message content."""
        # Create messages with different roles
        await chat_message.create(session, test_thread.id, "system", "System message")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "user", "First user message")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "assistant", "Assistant response")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "user", "Second user message")

        first_content = await chat_message.get_first_message_content(session, test_thread.id)

        assert first_content == "First user message"

    @pytest.mark.asyncio
    async def test_get_first_message_content_no_user_messages(self, session: Session, test_thread):
        """Test getting first user message when there are no user messages."""
        # Create only non-user messages
        await chat_message.create(session, test_thread.id, "system", "System message")
        await chat_message.create(session, test_thread.id, "assistant", "Assistant message")

        first_content = await chat_message.get_first_message_content(session, test_thread.id)

        assert first_content is None

    @pytest.mark.asyncio
    async def test_get_first_message_content_empty_thread(self, session: Session, test_thread):
        """Test getting first user message from empty thread."""
        first_content = await chat_message.get_first_message_content(session, test_thread.id)

        assert first_content is None

    @pytest.mark.asyncio
    async def test_delete_by_thread_id(self, session: Session, test_thread):
        """Test deleting all messages in a thread."""
        # Create some messages
        await chat_message.create(session, test_thread.id, "user", "Message 1")
        await chat_message.create(session, test_thread.id, "assistant", "Message 2")
        await chat_message.create(session, test_thread.id, "user", "Message 3")

        # Verify messages exist
        count_before = await chat_message.count_by_thread_id(session, test_thread.id)
        assert count_before == 3

        # Delete all messages
        deleted_count = await chat_message.delete_by_thread_id(session, test_thread.id)

        assert deleted_count == 3

        # Verify messages are deleted
        count_after = await chat_message.count_by_thread_id(session, test_thread.id)
        assert count_after == 0

    @pytest.mark.asyncio
    async def test_delete_by_thread_id_empty(self, session: Session, test_thread):
        """Test deleting messages from empty thread."""
        deleted_count = await chat_message.delete_by_thread_id(session, test_thread.id)

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_get_conversation_history_for_ai(self, session: Session, test_thread):
        """Test getting conversation history formatted for AI."""
        # Create a conversation
        await chat_message.create(session, test_thread.id, "user", "Hello")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "assistant", "Hi there!")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "user", "How are you?")
        time.sleep(0.01)
        await chat_message.create(session, test_thread.id, "assistant", "I'm doing well, thanks!")

        conversation = await chat_message.get_conversation_history_for_ai(session, test_thread.id)

        assert len(conversation) == 4
        assert conversation[0] == {"role": "user", "content": "Hello"}
        assert conversation[1] == {"role": "assistant", "content": "Hi there!"}
        assert conversation[2] == {"role": "user", "content": "How are you?"}
        assert conversation[3] == {"role": "assistant", "content": "I'm doing well, thanks!"}

    @pytest.mark.asyncio
    async def test_get_conversation_history_for_ai_with_limit(self, session: Session, test_thread):
        """Test getting conversation history with limit."""
        # Create 5 messages
        for i in range(5):
            role = "user" if i % 2 == 0 else "assistant"
            await chat_message.create(session, test_thread.id, role, f"Message {i + 1}")
            time.sleep(0.01)

        # Get only the 3 most recent
        conversation = await chat_message.get_conversation_history_for_ai(session, test_thread.id, limit=3)

        assert len(conversation) == 3
        assert conversation[0] == {"role": "user", "content": "Message 3"}
        assert conversation[1] == {"role": "assistant", "content": "Message 4"}
        assert conversation[2] == {"role": "user", "content": "Message 5"}

    @pytest.mark.asyncio
    async def test_get_conversation_history_for_ai_empty(self, session: Session, test_thread):
        """Test getting conversation history from empty thread."""
        conversation = await chat_message.get_conversation_history_for_ai(session, test_thread.id)

        assert len(conversation) == 0
        assert conversation == []

    @pytest.mark.asyncio
    async def test_thread_isolation(self, session: Session, test_user: User):
        """Test that messages are properly isolated by thread."""
        # Create two threads
        thread1 = await chat_thread.create(session, test_user.id, "Thread 1")
        thread2 = await chat_thread.create(session, test_user.id, "Thread 2")

        # Create messages in both threads
        await chat_message.create(session, thread1.id, "user", "Thread 1 Message")
        await chat_message.create(session, thread2.id, "user", "Thread 2 Message")

        # Verify thread isolation
        thread1_messages = await chat_message.find_by_thread_id(session, thread1.id)
        thread2_messages = await chat_message.find_by_thread_id(session, thread2.id)

        assert len(thread1_messages) == 1
        assert len(thread2_messages) == 1
        assert thread1_messages[0].content == "Thread 1 Message"
        assert thread2_messages[0].content == "Thread 2 Message"

        # Verify count isolation
        thread1_count = await chat_message.count_by_thread_id(session, thread1.id)
        thread2_count = await chat_message.count_by_thread_id(session, thread2.id)

        assert thread1_count == 1
        assert thread2_count == 1

    @pytest.mark.asyncio
    async def test_message_ordering_consistency(self, session: Session, test_thread):
        """Test that message ordering is consistent across different methods."""
        # Create messages with known order
        messages = []
        for i in range(5):
            message = await chat_message.create(session, test_thread.id, "user", f"Message {i + 1}")
            messages.append(message)
            time.sleep(0.01)  # Ensure different timestamps

        # Test different methods return consistent ordering
        all_messages = await chat_message.find_by_thread_id(session, test_thread.id)
        paginated_messages, _ = await chat_message.find_by_thread_id_paginated(
            session, test_thread.id, page=1, per_page=10
        )
        recent_messages = await chat_message.get_recent_messages_for_context(session, test_thread.id, limit=10)

        # All should be in chronological order (oldest first)
        for i in range(5):
            assert all_messages[i].content == f"Message {i + 1}"
            assert paginated_messages[i].content == f"Message {i + 1}"
            assert recent_messages[i].content == f"Message {i + 1}"
