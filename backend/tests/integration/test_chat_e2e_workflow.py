"""
End-to-end workflow tests for AI chat history feature.
Tests complete user workflows from thread creation to deletion.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from main import app


class TestChatE2EWorkflow:
    """End-to-end tests for complete chat workflows."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, test_user: User):
        """Setup authentication for all tests."""
        from app.services.auth import auth_user

        app.dependency_overrides[auth_user] = lambda: test_user
        yield
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    @patch("app.services.chat_service.AIHub")
    def test_complete_conversation_lifecycle(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test complete conversation lifecycle from creation to deletion."""
        # Mock AI Hub responses
        mock_ai_hub = AsyncMock()
        ai_responses = [
            "Hello! I'm here to help you with Python programming.",
            "Great question! Here are some Python learning resources...",
            "Absolutely! Let me explain functions in Python...",
            "You're welcome! Feel free to ask more questions.",
        ]
        mock_ai_hub.process_chat_message.side_effect = ai_responses
        mock_ai_hub_class.return_value = mock_ai_hub

        # 1. Start with empty thread list
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        assert response.json() == []

        # 2. Create new thread
        response = client.post("/api/chat/threads", json={"title": "Python Learning Session"})
        assert response.status_code == 201
        thread_data = response.json()
        thread_uuid = thread_data["uuid"]
        assert thread_data["title"] == "Python Learning Session"
        assert thread_data["message_count"] == 0

        # 3. Send first message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages",
            json={"content": "Hi, I want to learn Python programming. Can you help me?"},
        )
        assert response.status_code == 201
        ai_response1 = response.json()
        assert ai_response1["role"] == "assistant"
        assert ai_response1["content"] == ai_responses[0]

        # 4. Verify thread now has messages
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        thread_with_messages = response.json()
        assert thread_with_messages["thread"]["message_count"] == 2
        messages = thread_with_messages["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hi, I want to learn Python programming. Can you help me?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == ai_responses[0]

        # 5. Continue conversation with context
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "What are the best resources for beginners?"}
        )
        assert response.status_code == 201
        ai_response2 = response.json()
        assert ai_response2["content"] == ai_responses[1]

        # 6. Send third message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Can you explain how functions work?"}
        )
        assert response.status_code == 201
        ai_response3 = response.json()
        assert ai_response3["content"] == ai_responses[2]

        # 7. Send final message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Thank you for the explanation!"}
        )
        assert response.status_code == 201
        ai_response4 = response.json()
        assert ai_response4["content"] == ai_responses[3]

        # 8. Verify complete conversation
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        final_thread = response.json()
        assert final_thread["thread"]["message_count"] == 8  # 4 user + 4 AI

        messages = final_thread["messages"]
        assert len(messages) == 8

        # Verify conversation flow
        expected_messages = [
            ("user", "Hi, I want to learn Python programming. Can you help me?"),
            ("assistant", ai_responses[0]),
            ("user", "What are the best resources for beginners?"),
            ("assistant", ai_responses[1]),
            ("user", "Can you explain how functions work?"),
            ("assistant", ai_responses[2]),
            ("user", "Thank you for the explanation!"),
            ("assistant", ai_responses[3]),
        ]

        for i, (expected_role, expected_content) in enumerate(expected_messages):
            assert messages[i]["role"] == expected_role
            assert messages[i]["content"] == expected_content

        # 9. Verify thread appears in user's list
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 1
        assert threads[0]["uuid"] == thread_uuid
        assert threads[0]["message_count"] == 8

        # 10. Test conversation context
        response = client.get(f"/api/chat/threads/{thread_uuid}/context")
        assert response.status_code == 200
        context_data = response.json()
        assert context_data["context_messages"] == 8
        assert len(context_data["context"]) == 8

        # 11. Delete thread
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

        # 12. Verify thread is completely removed
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 404

        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        assert response.json() == []

        # 13. Verify AI Hub was called with proper context
        assert mock_ai_hub.process_chat_message.call_count == 4

        # Check that context was passed correctly (should increase with each call)
        calls = mock_ai_hub.process_chat_message.call_args_list
        # With the fix, history should not include the current message being sent
        assert len(calls[0][0][2]) == 0  # First call: no history
        assert len(calls[1][0][2]) == 2  # Second call: 2 messages history (user + AI)
        assert len(calls[2][0][2]) == 4  # Third call: 4 messages history
        assert len(calls[3][0][2]) == 6  # Fourth call: 6 messages history

    @patch("app.services.chat_service.AIHub")
    def test_multiple_threads_workflow(self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User):
        """Test managing multiple conversation threads."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "AI response"
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create multiple threads
        thread_uuids = []

        # Thread 1: Python discussion
        response = client.post("/api/chat/threads", json={"title": "Python Basics"})
        assert response.status_code == 201
        thread1_uuid = response.json()["uuid"]
        thread_uuids.append(thread1_uuid)

        # Thread 2: JavaScript discussion
        response = client.post("/api/chat/threads", json={"title": "JavaScript Fundamentals"})
        assert response.status_code == 201
        thread2_uuid = response.json()["uuid"]
        thread_uuids.append(thread2_uuid)

        # Thread 3: Database discussion
        response = client.post("/api/chat/threads", json={"title": "Database Design"})
        assert response.status_code == 201
        thread3_uuid = response.json()["uuid"]
        thread_uuids.append(thread3_uuid)

        # Add messages to each thread
        for i, thread_uuid in enumerate(thread_uuids):
            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": f"Question about topic {i + 1}"}
            )
            assert response.status_code == 201

        # Verify all threads exist
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 3

        # Threads should be ordered by updated_at (most recent first)
        thread_titles = [t["title"] for t in threads]
        assert "Database Design" in thread_titles
        assert "JavaScript Fundamentals" in thread_titles
        assert "Python Basics" in thread_titles

        # Test thread isolation - messages in one thread don't affect others
        response = client.get(f"/api/chat/threads/{thread1_uuid}")
        assert response.status_code == 200
        thread1_data = response.json()
        assert thread1_data["thread"]["message_count"] == 2  # 1 user + 1 AI

        response = client.get(f"/api/chat/threads/{thread2_uuid}")
        assert response.status_code == 200
        thread2_data = response.json()
        assert thread2_data["thread"]["message_count"] == 2  # 1 user + 1 AI

        # Delete middle thread
        response = client.delete(f"/api/chat/threads/{thread2_uuid}")
        assert response.status_code == 200

        # Verify only 2 threads remain
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 2

        remaining_uuids = [t["uuid"] for t in threads]
        assert thread1_uuid in remaining_uuids
        assert thread3_uuid in remaining_uuids
        assert thread2_uuid not in remaining_uuids

        # Cleanup remaining threads
        for uuid in [thread1_uuid, thread3_uuid]:
            response = client.delete(f"/api/chat/threads/{uuid}")
            assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_conversation_context_preservation(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that conversation context is properly preserved and passed to AI."""
        # Mock AI Hub to return different responses based on context
        mock_ai_hub = AsyncMock()

        def context_aware_response(message, user, history):
            if not history:
                return "Hello! How can I help you today?"
            elif len(history) == 2:
                return f"I see you mentioned '{history[0]['content']}'. Let me elaborate..."
            elif len(history) >= 4:
                return "Based on our conversation so far, here's what I recommend..."
            else:
                return "I understand. Please continue..."

        mock_ai_hub.process_chat_message.side_effect = context_aware_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Context Test"})
        assert response.status_code == 201
        thread_uuid = response.json()["uuid"]

        # Send first message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "I'm learning about machine learning"}
        )
        assert response.status_code == 201
        ai_response1 = response.json()
        assert ai_response1["content"] == "Hello! How can I help you today?"

        # Send second message - AI should reference first message
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "What algorithms should I start with?"}
        )
        assert response.status_code == 201
        ai_response2 = response.json()
        assert "I'm learning about machine learning" in ai_response2["content"]

        # Send third message - AI should have full context
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Can you give me a roadmap?"}
        )
        assert response.status_code == 201
        ai_response3 = response.json()
        assert "Based on our conversation so far" in ai_response3["content"]

        # Verify context was passed correctly to AI Hub
        calls = mock_ai_hub.process_chat_message.call_args_list
        assert len(calls) == 3

        # First call: no history
        assert len(calls[0][0][2]) == 0

        # Second call: 2 messages (user + AI)
        assert len(calls[1][0][2]) == 2
        assert calls[1][0][2][0]["content"] == "I'm learning about machine learning"

        # Third call: 4 messages
        assert len(calls[2][0][2]) == 4

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_failure_recovery(self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User):
        """Test system behavior when AI Hub fails."""
        # Mock AI Hub to fail initially, then recover
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = [
            Exception("AI Hub temporarily unavailable"),
            "I'm back online! How can I help?",
        ]
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Failure Recovery Test"})
        assert response.status_code == 201
        thread_uuid = response.json()["uuid"]

        # First message - AI Hub fails, should get fallback response
        with patch("app.services.chat_service.llm_chat_completions", return_value="Fallback response"):
            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello, are you there?"}
            )
            assert response.status_code == 201
            ai_response1 = response.json()
            assert ai_response1["content"] == "Fallback response"

        # Second message - AI Hub recovers
        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Can you hear me now?"})
        assert response.status_code == 201
        ai_response2 = response.json()
        assert ai_response2["content"] == "I'm back online! How can I help?"

        # Verify both messages were saved
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        thread_data = response.json()
        assert thread_data["thread"]["message_count"] == 4  # 2 user + 2 AI

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    def test_pagination_with_large_conversation(self, client: TestClient, session: Session, test_user: User):
        """Test pagination behavior with large conversations."""
        import asyncio

        # Create thread with many messages
        async def create_large_conversation():
            thread = await chat_thread.create(session, test_user.id, "Large Conversation")

            # Create 100 messages (50 exchanges)
            for i in range(50):
                await chat_message.create(session, thread.id, "user", f"User message {i + 1}")
                await chat_message.create(session, thread.id, "assistant", f"AI response {i + 1}")

            return thread

        thread = asyncio.run(create_large_conversation())

        # Test first page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=1&per_page=20")
        assert response.status_code == 200
        data = response.json()

        assert len(data["messages"]) == 20
        assert data["pagination"]["total_messages"] == 100
        assert data["pagination"]["total_pages"] == 5
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False

        # Test middle page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=3&per_page=20")
        assert response.status_code == 200
        data = response.json()

        assert len(data["messages"]) == 20
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is True

        # Test last page
        response = client.get(f"/api/chat/threads/{thread.uuid}?page=5&per_page=20")
        assert response.status_code == 200
        data = response.json()

        assert len(data["messages"]) == 20
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_prev"] is True

        # Test context with large conversation (should limit to recent messages)
        response = client.get(f"/api/chat/threads/{thread.uuid}/context?limit=10")
        assert response.status_code == 200
        context_data = response.json()

        assert context_data["context_messages"] == 10
        assert len(context_data["context"]) == 10

        # Should get the 10 most recent messages
        context = context_data["context"]
        assert "User message 46" in context[0]["content"]  # Messages 91-100 (last 10)
        assert "AI response 50" in context[-1]["content"]

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread.uuid}")
        assert response.status_code == 200

    def test_concurrent_message_sending(self, client: TestClient, session: Session, test_user: User):
        """Test handling of concurrent message sending to same thread."""
        from concurrent.futures import ThreadPoolExecutor

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Concurrency Test"})
        assert response.status_code == 201
        thread_uuid = response.json()["uuid"]

        # Mock AI Hub
        with patch("app.services.chat_service.AIHub") as mock_ai_hub_class:
            mock_ai_hub = AsyncMock()
            mock_ai_hub.process_chat_message.return_value = "Concurrent response"
            mock_ai_hub_class.return_value = mock_ai_hub

            # Send multiple messages concurrently
            def send_message(message_num):
                return client.post(
                    f"/api/chat/threads/{thread_uuid}/messages", json={"content": f"Concurrent message {message_num}"}
                )

            # Use ThreadPoolExecutor to send messages concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(send_message, i) for i in range(5)]
                responses = [future.result() for future in futures]

            # All requests should succeed
            for response in responses:
                assert response.status_code == 201

            # Verify all messages were saved
            response = client.get(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200
            thread_data = response.json()
            assert thread_data["thread"]["message_count"] == 10  # 5 user + 5 AI

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    def test_user_isolation_comprehensive(self, client: TestClient, session: Session, test_user: User):
        """Comprehensive test of user data isolation."""
        # Create another user
        other_user = User(
            id=999,
            clerk_sub="other_user_123",
            email="other@example.com",
            name="Other User",
            created_at=time.time(),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        # Create threads for both users directly in database
        import asyncio

        async def setup_user_data():
            # User 1 threads
            user1_thread1 = await chat_thread.create(session, test_user.id, "User 1 Thread 1")
            user1_thread2 = await chat_thread.create(session, test_user.id, "User 1 Thread 2")

            # User 2 threads
            user2_thread1 = await chat_thread.create(session, other_user.id, "User 2 Thread 1")
            user2_thread2 = await chat_thread.create(session, other_user.id, "User 2 Thread 2")

            # Add messages to each thread
            await chat_message.create(session, user1_thread1.id, "user", "User 1 message")
            await chat_message.create(session, user2_thread1.id, "user", "User 2 message")

            return user1_thread1, user1_thread2, user2_thread1, user2_thread2

        user1_t1, user1_t2, user2_t1, user2_t2 = asyncio.run(setup_user_data())

        # Test that user 1 can only see their own threads
        response = client.get("/api/chat/threads")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 2

        thread_titles = [t["title"] for t in threads]
        assert "User 1 Thread 1" in thread_titles
        assert "User 1 Thread 2" in thread_titles
        assert "User 2 Thread 1" not in thread_titles
        assert "User 2 Thread 2" not in thread_titles

        # Test that user 1 cannot access user 2's threads
        response = client.get(f"/api/chat/threads/{user2_t1.uuid}")
        assert response.status_code == 404

        response = client.post(f"/api/chat/threads/{user2_t1.uuid}/messages", json={"content": "Unauthorized message"})
        assert response.status_code == 404

        response = client.delete(f"/api/chat/threads/{user2_t1.uuid}")
        assert response.status_code == 404

        response = client.get(f"/api/chat/threads/{user2_t1.uuid}/context")
        assert response.status_code == 404

        # Cleanup user 1's threads
        for thread in [user1_t1, user1_t2]:
            response = client.delete(f"/api/chat/threads/{thread.uuid}")
            assert response.status_code == 200

        # Verify user 2's threads still exist in database
        import asyncio

        user2_threads = asyncio.run(chat_thread.find_by_user_id(session, other_user.id))
        assert len(user2_threads) == 2
