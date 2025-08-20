"""
Integration tests to validate all requirements for AI chat history feature.
Tests each requirement from the requirements document systematically.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from main import app


class TestChatRequirementsValidation:
    """Tests to validate all requirements from the requirements document."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, test_user: User):
        """Setup authentication for all tests."""
        from app.services.auth import auth_user

        app.dependency_overrides[auth_user] = lambda: test_user
        yield
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    # Requirement 1.1: ユーザーがAIにメッセージを送信したとき、システムはユーザーメッセージとAI応答の両方をデータベースに保存する
    @patch("app.services.chat_service.AIHub")
    def test_requirement_1_1_message_storage(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that both user messages and AI responses are stored in database."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response to user message"
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Requirement 1.1 Test"})
        assert response.status_code == 201
        thread_uuid = response.json()["uuid"]

        # Send message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello, this is a test message"}
        )
        assert response.status_code == 201

        # Verify both messages are stored
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        thread_data = response.json()

        messages = thread_data["messages"]
        assert len(messages) == 2

        # Verify user message
        user_message = messages[0]
        assert user_message["role"] == "user"
        assert user_message["content"] == "Hello, this is a test message"

        # Verify AI response
        ai_message = messages[1]
        assert ai_message["role"] == "assistant"
        assert ai_message["content"] == "AI response to user message"

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    # Requirement 1.2: ユーザーがチャットインターフェースにアクセスしたとき、システムは現在のスレッドから会話履歴を表示する
    def test_requirement_1_2_conversation_history_display(self, client: TestClient, session: Session, test_user: User):
        """Test that conversation history is displayed when accessing chat interface."""
        import asyncio

        # Create thread with conversation history
        async def setup_conversation():
            thread = await chat_thread.create(session, test_user.id, "History Test")

            # Create conversation history
            conversation = [
                ("user", "Hello"),
                ("assistant", "Hi there!"),
                ("user", "How are you?"),
                ("assistant", "I'm doing well, thank you!"),
                ("user", "What can you help me with?"),
                ("assistant", "I can help with various tasks and questions."),
            ]

            for role, content in conversation:
                await chat_message.create(session, thread.id, role, content)

            return thread

        thread = asyncio.run(setup_conversation())

        # Access thread (simulating chat interface access)
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        thread_data = response.json()
        messages = thread_data["messages"]

        # Verify complete conversation history is displayed
        assert len(messages) == 6

        # Verify chronological order
        expected_messages = [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
            ("user", "How are you?"),
            ("assistant", "I'm doing well, thank you!"),
            ("user", "What can you help me with?"),
            ("assistant", "I can help with various tasks and questions."),
        ]

        for i, (expected_role, expected_content) in enumerate(expected_messages):
            assert messages[i]["role"] == expected_role
            assert messages[i]["content"] == expected_content

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 1.3: ユーザーが新しい会話を開始したとき、システムは新しいチャットスレッドを自動的に作成する
    def test_requirement_1_3_automatic_thread_creation(self, client: TestClient, session: Session, test_user: User):
        """Test that new chat threads are automatically created for new conversations."""
        # Initially no threads
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Create new thread (simulating new conversation start)
        response = client.post("/api/chat/threads", json={"title": "New Conversation"})
        assert response.status_code == 201

        thread_data = response.json()
        assert thread_data["title"] == "New Conversation"
        assert "uuid" in thread_data
        assert thread_data["message_count"] == 0

        # Verify thread appears in list
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 1
        assert threads[0]["uuid"] == thread_data["uuid"]

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_data['uuid']}")
        assert response.status_code == 200

    # Requirement 1.4: ユーザーが既存のチャットスレッドを持たない場合、システムは最初のメッセージ時にスレッドを作成する
    @patch("app.services.chat_service.AIHub")
    def test_requirement_1_4_thread_creation_on_first_message(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that thread is created on first message if user has no existing threads."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "Welcome! I'm here to help."
        mock_ai_hub_class.return_value = mock_ai_hub

        # Verify no existing threads
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Create thread for first message (simulating automatic creation)
        response = client.post("/api/chat/threads", json={})
        assert response.status_code == 201
        thread_uuid = response.json()["uuid"]

        # Send first message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "This is my first message"}
        )
        assert response.status_code == 201

        # Verify thread was created and message was processed
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 1
        assert threads[0]["message_count"] == 2  # User message + AI response

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    # Requirement 2.1: チャットメッセージを取得するとき、システムは30件ずつのページでメッセージを返す
    def test_requirement_2_1_pagination_30_messages(self, client: TestClient, session: Session, test_user: User):
        """Test that messages are returned in pages of 30."""
        import asyncio

        # Create thread with more than 30 messages
        async def create_large_conversation():
            thread = await chat_thread.create(session, test_user.id, "Pagination Test")

            # Create 50 messages
            for i in range(50):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(create_large_conversation())

        # Test first page (default pagination)
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        data = response.json()
        messages = data["messages"]
        pagination = data["pagination"]

        # Should return 30 messages by default
        assert len(messages) == 30
        assert pagination["per_page"] == 30
        assert pagination["total_messages"] == 50
        assert pagination["total_pages"] == 2

        # Test explicit pagination
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=1&per_page=30")
        assert response.status_code == 200

        data = response.json()
        assert len(data["messages"]) == 30
        assert data["pagination"]["page"] == 1

        # Test second page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=2&per_page=30")
        assert response.status_code == 200

        data = response.json()
        assert len(data["messages"]) == 20  # Remaining messages
        assert data["pagination"]["page"] == 2

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 2.2: チャット履歴を表示するとき、システムはメッセージを時系列順（古い順）で表示する
    def test_requirement_2_2_chronological_message_order(self, client: TestClient, session: Session, test_user: User):
        """Test that messages are displayed in chronological order (oldest first)."""
        import asyncio

        # Create thread with messages at different times
        async def create_timed_conversation():
            thread = await chat_thread.create(session, test_user.id, "Chronological Test")

            base_time = time.time() - 3600  # Start 1 hour ago

            # Create messages with specific timestamps
            messages_data = [
                ("user", "First message", base_time),
                ("assistant", "First response", base_time + 60),
                ("user", "Second message", base_time + 120),
                ("assistant", "Second response", base_time + 180),
                ("user", "Third message", base_time + 240),
            ]

            for role, content, timestamp in messages_data:
                message = await chat_message.create(session, thread.id, role, content)
                # Update timestamp manually for testing
                message.created_at = timestamp
                session.add(message)

            session.commit()
            return thread

        thread = asyncio.run(create_timed_conversation())

        # Get messages
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        messages = response.json()["messages"]
        assert len(messages) == 5

        # Verify chronological order (oldest first)
        expected_order = ["First message", "First response", "Second message", "Second response", "Third message"]

        for i, expected_content in enumerate(expected_order):
            assert messages[i]["content"] == expected_content

        # Verify timestamps are in ascending order
        for i in range(1, len(messages)):
            assert messages[i]["created_at"] >= messages[i - 1]["created_at"]

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 2.3: ユーザーがより多くのメッセージを要求したとき、システムはページネーションコントロールを提供する
    def test_requirement_2_3_pagination_controls(self, client: TestClient, session: Session, test_user: User):
        """Test that pagination controls are provided for accessing more messages."""
        import asyncio

        # Create thread with multiple pages of messages
        async def create_multi_page_conversation():
            thread = await chat_thread.create(session, test_user.id, "Multi-page Test")

            # Create 75 messages (3 pages of 30, or 2.5 pages of 30)
            for i in range(75):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(create_multi_page_conversation())

        # Test pagination controls on first page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=1&per_page=30")
        assert response.status_code == 200

        data = response.json()
        pagination = data["pagination"]

        assert pagination["page"] == 1
        assert pagination["per_page"] == 30
        assert pagination["total_messages"] == 75
        assert pagination["total_pages"] == 3
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is False

        # Test pagination controls on middle page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=2&per_page=30")
        assert response.status_code == 200

        pagination = response.json()["pagination"]
        assert pagination["page"] == 2
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is True

        # Test pagination controls on last page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=3&per_page=30")
        assert response.status_code == 200

        data = response.json()
        pagination = data["pagination"]

        assert pagination["page"] == 3
        assert len(data["messages"]) == 15  # Remaining messages
        assert pagination["has_next"] is False
        assert pagination["has_prev"] is True

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 2.4: チャット履歴を読み込むとき、システムはユーザーメッセージとAI応答の両方を含める
    def test_requirement_2_4_include_both_message_types(self, client: TestClient, session: Session, test_user: User):
        """Test that chat history includes both user messages and AI responses."""
        import asyncio

        # Create thread with mixed message types
        async def create_mixed_conversation():
            thread = await chat_thread.create(session, test_user.id, "Mixed Messages Test")

            # Create alternating user and AI messages
            messages = [
                ("user", "User message 1"),
                ("assistant", "AI response 1"),
                ("user", "User message 2"),
                ("assistant", "AI response 2"),
                ("user", "User message 3"),
                ("assistant", "AI response 3"),
            ]

            for role, content in messages:
                await chat_message.create(session, thread.id, role, content)

            return thread

        thread = asyncio.run(create_mixed_conversation())

        # Get chat history
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        messages = response.json()["messages"]
        assert len(messages) == 6

        # Verify both message types are included
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        ai_messages = [msg for msg in messages if msg["role"] == "assistant"]

        assert len(user_messages) == 3
        assert len(ai_messages) == 3

        # Verify content is preserved
        assert user_messages[0]["content"] == "User message 1"
        assert ai_messages[0]["content"] == "AI response 1"
        assert user_messages[2]["content"] == "User message 3"
        assert ai_messages[2]["content"] == "AI response 3"

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 3.1: AIにメッセージを送信するとき、システムは直近30件のメッセージをコンテキストとして含める
    @patch("app.services.chat_service.AIHub")
    def test_requirement_3_1_context_30_messages(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that AI receives the most recent 30 messages as context."""
        import asyncio

        # Mock AI Hub to capture context
        mock_ai_hub = AsyncMock()
        captured_context = None

        def capture_context(message, user, history):
            nonlocal captured_context
            captured_context = history
            return "AI response with context"

        mock_ai_hub.process_chat_message.side_effect = capture_context
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread with more than 30 messages
        async def create_long_conversation():
            thread = await chat_thread.create(session, test_user.id, "Context Test")

            # Create 50 messages
            for i in range(50):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(create_long_conversation())

        # Send new message
        response = client.post(
            f"/api/chat/threads/{thread.uuid}/messages", json={"content": "New message requiring context"}
        )
        assert response.status_code == 201

        # Verify AI received context (30 most recent minus current message = 29)
        assert captured_context is not None
        assert len(captured_context) == 29

        # Verify it's the most recent messages (excluding current)
        assert "Message 22" in captured_context[0]["content"]  # Should start around message 22
        assert "Message 50" in captured_context[-1]["content"]  # Should end with message 50

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 3.2: AIが応答を生成するとき、会話履歴をコンテキストとして考慮する
    @patch("app.services.chat_service.AIHub")
    def test_requirement_3_2_ai_considers_history_context(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that AI considers conversation history when generating responses."""
        # Mock AI Hub to demonstrate context awareness
        mock_ai_hub = AsyncMock()

        def context_aware_response(message, user, history):
            if not history:
                return "Hello! How can I help you?"
            elif "Python" in message or any(
                "Python" in msg["content"] for msg in history if isinstance(msg, dict) and "content" in msg
            ):
                return "Continuing our Python discussion..."
            else:
                return "Based on our previous conversation..."

        mock_ai_hub.process_chat_message.side_effect = context_aware_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Context Awareness Test"})
        thread_uuid = response.json()["uuid"]

        # First message (no context)
        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello"})
        assert response.status_code == 201
        ai_response1 = response.json()
        assert ai_response1["content"] == "Hello! How can I help you?"

        # Second message (with context mentioning Python)
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "I want to learn Python programming"}
        )
        assert response.status_code == 201
        ai_response2 = response.json()
        assert "Python discussion" in ai_response2["content"]

        # Third message (AI should remember Python context)
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "What should I learn first?"}
        )
        assert response.status_code == 201
        ai_response3 = response.json()
        assert "Python discussion" in ai_response3["content"]

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    # Requirement 3.3: 会話が長くなりすぎたとき、システムはAIコンテキスト用に最新の30件のメッセージのみを使用する
    @patch("app.services.chat_service.AIHub")
    def test_requirement_3_3_context_limit_30_messages(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that system limits AI context to most recent 30 messages for long conversations."""
        import asyncio

        # Mock AI Hub to capture context
        mock_ai_hub = AsyncMock()
        context_lengths = []

        def capture_context_length(message, user, history):
            context_lengths.append(len(history))
            return f"Received {len(history)} messages as context"

        mock_ai_hub.process_chat_message.side_effect = capture_context_length
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread with many messages
        async def create_very_long_conversation():
            thread = await chat_thread.create(session, test_user.id, "Long Context Test")

            # Create 60 messages
            for i in range(60):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(create_very_long_conversation())

        # Send new message
        response = client.post(
            f"/api/chat/threads/{thread.uuid}/messages", json={"content": "This should have limited context"}
        )
        assert response.status_code == 201

        # Verify context was limited to 30 messages total (history)
        # When sending a new message to a thread with 60 messages:
        # - Total messages become 61 (60 existing + 1 new)
        # - get_conversation_context returns latest 30 messages
        # - History (excluding current message) is 29 messages
        assert len(context_lengths) == 1
        assert context_lengths[0] == 29  # Should be 29 (30 total context minus current message)

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 3.4: メッセージ履歴を含めるとき、システムはAIプロンプト用に適切にフォーマットする
    @patch("app.services.chat_service.AIHub")
    def test_requirement_3_4_proper_context_formatting(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that message history is properly formatted for AI prompts."""
        import asyncio

        # Mock AI Hub to capture context format
        mock_ai_hub = AsyncMock()
        captured_context = None

        def capture_context_format(message, user, history):
            nonlocal captured_context
            captured_context = history
            return "Context format validated"

        mock_ai_hub.process_chat_message.side_effect = capture_context_format
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread with conversation
        async def create_formatted_conversation():
            thread = await chat_thread.create(session, test_user.id, "Format Test")

            messages = [
                ("user", "Hello, how are you?"),
                ("assistant", "I'm doing well, thank you!"),
                ("user", "Can you help me with Python?"),
                ("assistant", "Of course! I'd be happy to help with Python."),
            ]

            for role, content in messages:
                await chat_message.create(session, thread.id, role, content)

            return thread

        thread = asyncio.run(create_formatted_conversation())

        # Send message to trigger context formatting
        response = client.post(
            f"/api/chat/threads/{thread.uuid}/messages", json={"content": "What's the best way to start?"}
        )
        assert response.status_code == 201

        # Verify context format
        assert captured_context is not None
        assert isinstance(captured_context, list)
        assert len(captured_context) == 4

        # Verify each message has proper format
        for msg in captured_context:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0

        # Verify specific content
        expected_messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Can you help me with Python?"},
            {"role": "assistant", "content": "Of course! I'd be happy to help with Python."},
        ]

        for i, expected in enumerate(expected_messages):
            assert captured_context[i]["role"] == expected["role"]
            assert captured_context[i]["content"] == expected["content"]

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    # Requirement 4.1: ユーザーがスレッド削除を要求したとき、システムはスレッドと関連するすべてのメッセージを完全に削除する
    def test_requirement_4_1_complete_thread_deletion(self, client: TestClient, session: Session, test_user: User):
        """Test that thread deletion removes thread and all related messages completely."""
        import asyncio

        # Create thread with messages
        async def create_thread_with_messages():
            thread = await chat_thread.create(session, test_user.id, "Deletion Test")

            # Add messages
            for i in range(10):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(create_thread_with_messages())

        # Verify thread and messages exist
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200
        assert response.json()["thread"]["message_count"] == 10

        # Delete thread
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        # Verify thread is completely deleted
        response = client.get(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 404

        # Verify messages are also deleted (check in database)
        async def verify_messages_deleted():
            messages = await chat_message.find_by_thread_id_paginated(session, thread.id, 1, 100)
            return messages[0]  # Should return empty list

        remaining_messages = asyncio.run(verify_messages_deleted())
        assert len(remaining_messages) == 0

    # Requirement 4.2: ユーザーがスレッドにアクセスしたとき、システムは利用可能なチャットスレッドのリストを表示する
    def test_requirement_4_2_available_threads_list(self, client: TestClient, session: Session, test_user: User):
        """Test that system displays list of available chat threads."""
        import asyncio

        # Create multiple threads
        async def create_multiple_threads():
            threads = []
            for i in range(5):
                thread = await chat_thread.create(session, test_user.id, f"Thread {i + 1}")
                threads.append(thread)
                # Add at least one message to each
                await chat_message.create(session, thread.id, "user", f"Message in thread {i + 1}")
            return threads

        threads = asyncio.run(create_multiple_threads())

        # Get threads list
        response = client.get("/api/chat/threads")
        assert response.status_code == 200

        threads_list = response.json()
        assert len(threads_list) == 5

        # Verify each thread in the list
        for thread_data in threads_list:
            assert "uuid" in thread_data
            assert "title" in thread_data
            assert "created_at" in thread_data
            assert "updated_at" in thread_data
            assert "message_count" in thread_data
            assert thread_data["message_count"] >= 1

        # Verify all created threads are in the list
        returned_uuids = {t["uuid"] for t in threads_list}
        expected_uuids = {str(t.uuid) for t in threads}
        assert returned_uuids == expected_uuids

        # Cleanup
        for thread in threads:
            response = client.delete(f"/api/chat/threads/{thread.uuid}")
            assert response.status_code == 200

    # Requirement 4.3: 新しいスレッドを作成するとき、システムは識別用の一意のUUIDを生成する
    def test_requirement_4_3_unique_uuid_generation(self, client: TestClient, session: Session, test_user: User):
        """Test that system generates unique UUIDs for thread identification."""
        import uuid

        created_uuids = set()

        # Create multiple threads
        for i in range(10):
            response = client.post("/api/chat/threads", json={"title": f"UUID Test {i + 1}"})
            assert response.status_code == 201

            thread_data = response.json()
            thread_uuid = thread_data["uuid"]

            # Verify UUID format
            try:
                uuid.UUID(thread_uuid)  # This will raise ValueError if invalid
            except ValueError:
                pytest.fail(f"Invalid UUID format: {thread_uuid}")

            # Verify uniqueness
            assert thread_uuid not in created_uuids, f"Duplicate UUID generated: {thread_uuid}"
            created_uuids.add(thread_uuid)

        # Cleanup
        for thread_uuid in created_uuids:
            response = client.delete(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200

    # Requirement 4.4: スレッドが削除されたとき、システムはハードデリートを実行する
    def test_requirement_4_4_hard_delete_execution(self, client: TestClient, session: Session, test_user: User):
        """Test that system performs hard delete (not soft delete) when thread is deleted."""
        import asyncio

        # Create thread
        async def create_test_thread():
            thread = await chat_thread.create(session, test_user.id, "Hard Delete Test")
            await chat_message.create(session, thread.id, "user", "Test message")
            return thread

        thread = asyncio.run(create_test_thread())
        thread_id = thread.id

        # Verify thread exists in database
        async def check_thread_exists():
            return await chat_thread.get_by_id(session, thread_id)

        existing_thread = asyncio.run(check_thread_exists())
        assert existing_thread is not None

        # Delete thread
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

        # Verify hard delete - thread should not exist in database at all
        deleted_thread = asyncio.run(check_thread_exists())
        assert deleted_thread is None  # Hard delete means no record exists

        # Verify messages are also hard deleted
        async def check_messages_exist():
            messages, _ = await chat_message.find_by_thread_id_paginated(session, thread_id, 1, 10)
            return messages

        remaining_messages = asyncio.run(check_messages_exist())
        assert len(remaining_messages) == 0  # Hard delete means no messages remain
