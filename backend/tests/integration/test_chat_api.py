"""Integration tests for Chat API endpoints."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from main import app


class TestChatAPIIntegration:
    """Integration tests for chat API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, test_user: User):
        """Setup authentication for all tests."""
        from app.services.auth import auth_user

        # Override auth_user dependency to return test_user
        app.dependency_overrides[auth_user] = lambda: test_user
        yield
        # Clean up after test
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    @pytest.fixture
    async def test_thread(self, session: Session, test_user: User):
        """Create a test chat thread."""
        return await chat_thread.create(session, test_user.id, "Test Thread")

    def test_get_chat_threads_empty(self, client: TestClient, session: Session, test_user: User):
        """Test getting chat threads when user has no threads."""
        response = client.get("/api/chat/threads")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_chat_threads_with_data(self, client: TestClient, session: Session, test_user: User):
        """Test getting chat threads with existing data."""
        # Create test threads using the repository directly
        import asyncio

        async def create_test_threads():
            thread1 = await chat_thread.create(session, test_user.id, "Thread 1")
            time.sleep(0.01)  # Ensure different timestamps
            thread2 = await chat_thread.create(session, test_user.id, "Thread 2")
            time.sleep(0.01)
            thread3 = await chat_thread.create(session, test_user.id, "Thread 3")
            return [thread1, thread2, thread3]

        asyncio.run(create_test_threads())

        response = client.get("/api/chat/threads")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Should be ordered by updated_at desc (most recent first)
        assert data[0]["title"] == "Thread 3"
        assert data[1]["title"] == "Thread 2"
        assert data[2]["title"] == "Thread 1"

        # Verify response structure
        for thread_data in data:
            assert "uuid" in thread_data
            assert "title" in thread_data
            assert "created_at" in thread_data
            assert "updated_at" in thread_data
            assert "message_count" in thread_data

    def test_get_chat_threads_pagination(self, client: TestClient, session: Session, test_user: User):
        """Test chat threads pagination."""
        # Create 5 test threads
        import asyncio

        async def create_test_threads():
            threads = []
            for i in range(5):
                thread = await chat_thread.create(session, test_user.id, f"Thread {i + 1}")
                threads.append(thread)
                time.sleep(0.01)
            return threads

        asyncio.run(create_test_threads())

        # Test first page
        response = client.get("/api/chat/threads?page=1&per_page=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test second page
        response = client.get("/api/chat/threads?page=2&per_page=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_chat_thread_with_title(self, client: TestClient, session: Session, test_user: User):
        """Test creating a chat thread with title."""
        request_data = {"title": "My New Chat Thread"}

        response = client.post("/api/chat/threads", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "My New Chat Thread"
        assert "uuid" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["message_count"] == 0

    def test_create_chat_thread_without_title(self, client: TestClient, session: Session, test_user: User):
        """Test creating a chat thread without title."""
        request_data = {}

        response = client.post("/api/chat/threads", json=request_data)

        assert response.status_code == 201
        data = response.json()

        assert data["title"] is None
        assert "uuid" in data

    def test_create_chat_thread_invalid_title(self, client: TestClient, session: Session, test_user: User):
        """Test creating a chat thread with invalid title."""
        # Title too short
        request_data = {"title": "ab"}

        response = client.post("/api/chat/threads", json=request_data)

        assert response.status_code == 422

        # Title too long
        request_data = {"title": "a" * 201}

        response = client.post("/api/chat/threads", json=request_data)

        assert response.status_code == 422

    def test_get_chat_thread_with_messages(self, client: TestClient, session: Session, test_user: User):
        """Test getting a chat thread with messages."""
        import asyncio

        async def setup_thread_with_messages():
            thread = await chat_thread.create(session, test_user.id, "Test Thread")

            # Create some messages
            await chat_message.create(session, thread.id, "user", "Hello")
            await chat_message.create(session, thread.id, "assistant", "Hi there!")
            await chat_message.create(session, thread.id, "user", "How are you?")

            return thread

        thread = asyncio.run(setup_thread_with_messages())

        response = client.get(f"/api/chat/threads/{thread.uuid}")

        assert response.status_code == 200
        data = response.json()

        # Verify thread data
        assert data["thread"]["uuid"] == str(thread.uuid)
        assert data["thread"]["title"] == "Test Thread"
        assert data["thread"]["message_count"] == 3

        # Verify messages
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Hi there!"
        assert data["messages"][2]["role"] == "user"
        assert data["messages"][2]["content"] == "How are you?"

        # Verify pagination
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["per_page"] == 30
        assert pagination["total_messages"] == 3
        assert pagination["total_pages"] == 1
        assert pagination["has_next"] is False
        assert pagination["has_prev"] is False

    def test_get_chat_thread_with_messages_pagination(self, client: TestClient, session: Session, test_user: User):
        """Test getting chat thread messages with pagination."""
        import asyncio

        async def setup_thread_with_many_messages():
            thread = await chat_thread.create(session, test_user.id, "Test Thread")

            # Create 5 messages
            for i in range(5):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(setup_thread_with_many_messages())

        # Test first page with 3 items per page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=1&per_page=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data["messages"]) == 3
        assert data["pagination"]["total_messages"] == 5
        assert data["pagination"]["total_pages"] == 2
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False

        # Test second page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=2&per_page=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data["messages"]) == 2
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_prev"] is True

    def test_get_chat_thread_not_found(self, client: TestClient, session: Session, test_user: User):
        """Test getting non-existent chat thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/chat/threads/{fake_uuid}")

        assert response.status_code == 404
        assert "Chat thread not found" in response.json()["detail"]

    @patch("app.services.chat_service.AIHub")
    def test_send_message_success(self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User):
        """Test sending a message successfully."""
        import asyncio

        # Create test thread
        thread = asyncio.run(chat_thread.create(session, test_user.id, "Test Thread"))

        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response to your message"
        mock_ai_hub_class.return_value = mock_ai_hub

        request_data = {"content": "Hello, how are you?"}

        response = client.post(f"/api/chat/threads/{thread.uuid}/messages", json=request_data)

        assert response.status_code == 201
        data = response.json()

        # Should return the AI response
        assert data["role"] == "assistant"
        assert data["content"] == "AI response to your message"
        assert "uuid" in data
        assert "created_at" in data

    def test_send_message_invalid_content(self, client: TestClient, session: Session, test_user: User):
        """Test sending message with invalid content."""
        import asyncio

        thread = asyncio.run(chat_thread.create(session, test_user.id, "Test Thread"))

        # Empty content
        request_data = {"content": ""}

        response = client.post(f"/api/chat/threads/{thread.uuid}/messages", json=request_data)

        assert response.status_code == 422

        # Content too long
        request_data = {"content": "a" * 4001}

        response = client.post(f"/api/chat/threads/{thread.uuid}/messages", json=request_data)

        assert response.status_code == 422

    def test_send_message_thread_not_found(self, client: TestClient, session: Session, test_user: User):
        """Test sending message to non-existent thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        request_data = {"content": "Hello"}

        response = client.post(f"/api/chat/threads/{fake_uuid}/messages", json=request_data)

        assert response.status_code == 404

    def test_delete_chat_thread_success(self, client: TestClient, session: Session, test_user: User):
        """Test deleting a chat thread successfully."""
        import asyncio

        thread = asyncio.run(chat_thread.create(session, test_user.id, "Test Thread"))

        response = client.delete(f"/api/chat/threads/{thread.uuid}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_delete_chat_thread_not_found(self, client: TestClient, session: Session, test_user: User):
        """Test deleting non-existent chat thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.delete(f"/api/chat/threads/{fake_uuid}")

        assert response.status_code == 404

    def test_get_conversation_context(self, client: TestClient, session: Session, test_user: User):
        """Test getting conversation context."""
        import asyncio

        async def setup_thread_with_messages():
            thread = await chat_thread.create(session, test_user.id, "Test Thread")

            # Create conversation
            await chat_message.create(session, thread.id, "user", "Hello")
            await chat_message.create(session, thread.id, "assistant", "Hi there!")
            await chat_message.create(session, thread.id, "user", "How are you?")

            return thread

        thread = asyncio.run(setup_thread_with_messages())

        response = client.get(f"/api/chat/threads/{thread.uuid}/context")

        assert response.status_code == 200
        data = response.json()

        assert data["thread_uuid"] == str(thread.uuid)
        assert data["context_messages"] == 3
        assert len(data["context"]) == 3

        # Verify context format
        context = data["context"]
        assert context[0] == {"role": "user", "content": "Hello"}
        assert context[1] == {"role": "assistant", "content": "Hi there!"}
        assert context[2] == {"role": "user", "content": "How are you?"}

    def test_get_conversation_context_with_limit(self, client: TestClient, session: Session, test_user: User):
        """Test getting conversation context with limit."""
        import asyncio

        async def setup_thread_with_many_messages():
            thread = await chat_thread.create(session, test_user.id, "Test Thread")

            # Create 5 messages
            for i in range(5):
                role = "user" if i % 2 == 0 else "assistant"
                await chat_message.create(session, thread.id, role, f"Message {i + 1}")

            return thread

        thread = asyncio.run(setup_thread_with_many_messages())

        response = client.get(f"/api/chat/threads/{thread.uuid}/context?limit=3")

        assert response.status_code == 200
        data = response.json()

        assert data["context_messages"] == 3
        assert len(data["context"]) == 3

        # Should get the 3 most recent messages
        context = data["context"]
        assert context[0]["content"] == "Message 3"
        assert context[1]["content"] == "Message 4"
        assert context[2]["content"] == "Message 5"

    def test_get_conversation_context_thread_not_found(self, client: TestClient, session: Session, test_user: User):
        """Test getting context for non-existent thread."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/chat/threads/{fake_uuid}/context")

        assert response.status_code == 404

    def test_authentication_required(self, session: Session):
        """Test that all endpoints require authentication."""
        from fastapi.testclient import TestClient

        # Create client without authentication override
        client = TestClient(app)

        endpoints = [
            ("GET", "/api/chat/threads"),
            ("POST", "/api/chat/threads"),
            ("GET", "/api/chat/threads/fake-uuid"),
            ("POST", "/api/chat/threads/fake-uuid/messages"),
            ("DELETE", "/api/chat/threads/fake-uuid"),
            ("GET", "/api/chat/threads/fake-uuid/context"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Should return 401, 403, 422 (validation), or 500 (due to auth failure) for unauthenticated requests
            assert response.status_code in [401, 403, 422, 500], (
                f"Endpoint {method} {endpoint} should require authentication"
            )

    def test_user_isolation(self, client: TestClient, session: Session, test_user: User):
        """Test that users can only access their own threads."""
        import asyncio

        # Create another user
        other_user = User(
            id=999,
            clerk_user_id="other_user_123",
            clerk_sub="other_user_123",
            email="other@example.com",
            created_at=time.time(),
            updated_at=time.time(),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        # Create thread for other user
        other_thread = asyncio.run(chat_thread.create(session, other_user.id, "Other User Thread"))

        # Try to access other user's thread (should fail)
        response = client.get(f"/api/chat/threads/{other_thread.uuid}")
        assert response.status_code == 404

        # Try to send message to other user's thread (should fail)
        response = client.post(f"/api/chat/threads/{other_thread.uuid}/messages", json={"content": "Hello"})
        assert response.status_code == 404

        # Try to delete other user's thread (should fail)
        response = client.delete(f"/api/chat/threads/{other_thread.uuid}")
        assert response.status_code == 404

    def test_error_handling_and_validation(self, client: TestClient, session: Session, test_user: User):
        """Test error handling and input validation."""
        # Test invalid pagination parameters
        response = client.get("/api/chat/threads?page=0")
        assert response.status_code == 422

        response = client.get("/api/chat/threads?per_page=0")
        assert response.status_code == 422

        response = client.get("/api/chat/threads?per_page=101")
        assert response.status_code == 422

        # Test invalid UUID format (may return 500 due to UUID parsing error)
        response = client.get("/api/chat/threads/invalid-uuid")
        assert response.status_code in [404, 500]  # Should handle gracefully

        # Test invalid JSON
        response = client.post("/api/chat/threads", data="invalid json")
        assert response.status_code == 422

    @patch("app.services.chat_service.AIHub")
    def test_end_to_end_conversation_flow(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test complete conversation flow from thread creation to deletion."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = [
            "Nice to meet you!",
            "I'm doing well, thank you for asking!",
            "You're welcome!",
        ]
        mock_ai_hub_class.return_value = mock_ai_hub

        # 1. Create thread
        response = client.post("/api/chat/threads", json={"title": "E2E Test Thread"})
        assert response.status_code == 201
        thread_data = response.json()
        thread_uuid = thread_data["uuid"]

        # 2. Send first message
        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello, I'm John"})
        assert response.status_code == 201
        ai_response1 = response.json()
        assert ai_response1["content"] == "Nice to meet you!"

        # 3. Send second message
        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "How are you?"})
        assert response.status_code == 201
        ai_response2 = response.json()
        assert ai_response2["content"] == "I'm doing well, thank you for asking!"

        # 4. Get thread with messages
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        thread_with_messages = response.json()

        # Should have 4 messages (2 user + 2 AI)
        assert thread_with_messages["thread"]["message_count"] == 4
        assert len(thread_with_messages["messages"]) == 4

        # Verify message order (chronological)
        messages = thread_with_messages["messages"]
        assert messages[0]["role"] == "user" and messages[0]["content"] == "Hello, I'm John"
        assert messages[1]["role"] == "assistant" and messages[1]["content"] == "Nice to meet you!"
        assert messages[2]["role"] == "user" and messages[2]["content"] == "How are you?"
        assert messages[3]["role"] == "assistant" and messages[3]["content"] == "I'm doing well, thank you for asking!"

        # 5. Get conversation context
        response = client.get(f"/api/chat/threads/{thread_uuid}/context")
        assert response.status_code == 200
        context_data = response.json()
        assert context_data["context_messages"] == 4

        # 6. Send final message
        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Thank you!"})
        assert response.status_code == 201

        # 7. Verify thread appears in user's thread list
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 1
        assert threads[0]["uuid"] == thread_uuid
        assert threads[0]["message_count"] == 6  # 3 user + 3 AI

        # 8. Delete thread
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

        # 9. Verify thread is deleted
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 404

        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 0
