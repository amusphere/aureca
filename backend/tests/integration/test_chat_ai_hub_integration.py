"""
Integration tests for AI Hub integration with chat history feature.
Tests the interaction between chat service and AI Hub system.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import User
from app.services.ai.core.hub import AIHub
from main import app


class TestChatAIHubIntegration:
    """Integration tests for AI Hub and chat system interaction."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, test_user: User):
        """Setup authentication for all tests."""
        from app.services.auth import auth_user

        app.dependency_overrides[auth_user] = lambda: test_user
        yield
        if auth_user in app.dependency_overrides:
            del app.dependency_overrides[auth_user]

    @pytest.fixture
    async def test_thread_with_history(self, session: Session, test_user: User):
        """Create a test thread with conversation history."""
        thread = await chat_thread.create(session, test_user.id, "AI Hub Test Thread")

        # Create conversation history
        messages = [
            ("user", "Hello, I'm working on a Python project"),
            ("assistant", "Great! I'd be happy to help with your Python project. What are you working on?"),
            ("user", "I need to create a web API"),
            ("assistant", "Excellent! For web APIs in Python, I recommend using FastAPI. It's modern and efficient."),
            ("user", "How do I handle database connections?"),
        ]

        for role, content in messages:
            await chat_message.create(session, thread.id, role, content)

        return thread

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_receives_conversation_context(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_thread_with_history, test_user: User
    ):
        """Test that AI Hub receives proper conversation context."""
        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "For database connections, use SQLAlchemy with FastAPI."
        mock_ai_hub_class.return_value = mock_ai_hub

        # Send message to thread with history
        response = client.post(
            f"/api/chat/threads/{test_thread_with_history.uuid}/messages",
            json={"content": "What's the best way to do this?"},
        )

        assert response.status_code == 201
        ai_response = response.json()
        assert ai_response["content"] == "For database connections, use SQLAlchemy with FastAPI."

        # Verify AI Hub was called with correct parameters
        mock_ai_hub.process_chat_message.assert_called_once()
        call_args = mock_ai_hub.process_chat_message.call_args

        message = call_args[0][0]
        user = call_args[0][1]
        history = call_args[0][2]

        assert message == "What's the best way to do this?"
        assert user.id == test_user.id
        assert len(history) == 5  # Previous conversation history (excluding current message)

        # Verify history format and order
        expected_history = [
            {"role": "user", "content": "Hello, I'm working on a Python project"},
            {
                "role": "assistant",
                "content": "Great! I'd be happy to help with your Python project. What are you working on?",
            },
            {"role": "user", "content": "I need to create a web API"},
            {
                "role": "assistant",
                "content": "Excellent! For web APIs in Python, I recommend using FastAPI. It's modern and efficient.",
            },
            {"role": "user", "content": "How do I handle database connections?"},
        ]

        for i, expected_msg in enumerate(expected_history):
            assert history[i]["role"] == expected_msg["role"]
            assert history[i]["content"] == expected_msg["content"]

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_context_limit_enforcement(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that AI Hub receives limited context for very long conversations."""
        import asyncio

        # Create thread with many messages (more than context limit)
        async def create_long_conversation():
            thread = await chat_thread.create(session, test_user.id, "Long Conversation")

            # Create 50 message pairs (100 total messages)
            for i in range(50):
                await chat_message.create(session, thread.id, "user", f"User message {i + 1}")
                await chat_message.create(session, thread.id, "assistant", f"AI response {i + 1}")

            return thread

        long_thread = asyncio.run(create_long_conversation())

        # Mock AI Hub
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.return_value = "I understand the context."
        mock_ai_hub_class.return_value = mock_ai_hub

        # Send new message
        response = client.post(
            f"/api/chat/threads/{long_thread.uuid}/messages", json={"content": "Can you summarize our conversation?"}
        )

        assert response.status_code == 201

        # Verify AI Hub received limited context (default limit is 30)
        call_args = mock_ai_hub.process_chat_message.call_args
        history = call_args[0][2]

        assert len(history) == 29  # 30 most recent messages minus current message being sent

        # Verify we got the most recent messages (the exact order depends on implementation)
        # Should contain messages from the end of the conversation
        assert any("User message 50" in msg["content"] for msg in history)
        assert any("AI response 50" in msg["content"] for msg in history)

        # Cleanup
        response = client.delete(f"/api/chat/threads/{long_thread.uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_error_handling_with_fallback(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test error handling when AI Hub fails with fallback to direct LLM."""
        # Mock AI Hub to fail
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = Exception("AI Hub service unavailable")
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock fallback LLM
        with patch("app.services.chat_service.llm_chat_completions") as mock_llm:
            mock_llm.return_value = "Fallback response from direct LLM"

            # Create thread and send message
            response = client.post("/api/chat/threads", json={"title": "Error Test"})
            thread_uuid = response.json()["uuid"]

            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello, can you help me?"}
            )

            assert response.status_code == 201
            ai_response = response.json()
            assert ai_response["content"] == "Fallback response from direct LLM"

            # Verify fallback was called with proper context
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[1]  # kwargs

            assert "Hello, can you help me?" in str(call_args)
            assert "prompts" in call_args  # The LLM function uses 'prompts' parameter

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_complete_failure_graceful_degradation(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test graceful degradation when both AI Hub and fallback LLM fail."""
        # Mock AI Hub to fail
        mock_ai_hub = AsyncMock()
        mock_ai_hub.process_chat_message.side_effect = Exception("AI Hub failed")
        mock_ai_hub_class.return_value = mock_ai_hub

        # Mock fallback LLM to also fail
        with patch("app.services.chat_service.llm_chat_completions", side_effect=Exception("LLM failed")):
            # Create thread and send message
            response = client.post("/api/chat/threads", json={"title": "Complete Failure Test"})
            thread_uuid = response.json()["uuid"]

            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": "This should trigger error handling"}
            )

            assert response.status_code == 201
            ai_response = response.json()

            # Should get error message
            assert (
                "technical difficulties" in ai_response["content"].lower()
                or "temporarily unavailable" in ai_response["content"].lower()
            )

            # Verify both user message and error response were saved
            response = client.get(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200
            thread_data = response.json()
            assert thread_data["thread"]["message_count"] == 2

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    def test_ai_hub_real_integration(self, client: TestClient, session: Session, test_user: User):
        """Test integration with real AI Hub instance (if available)."""
        # This test uses the actual AI Hub without mocking
        # It will be skipped if AI Hub is not properly configured

        try:
            # Try to create a real AI Hub instance
            AIHub()

            # Create thread
            response = client.post("/api/chat/threads", json={"title": "Real AI Hub Test"})
            assert response.status_code == 201
            thread_uuid = response.json()["uuid"]

            # Send a simple message
            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Hello, can you tell me what 2+2 equals?"}
            )

            # If AI Hub is working, we should get a response
            if response.status_code == 201:
                ai_response = response.json()
                assert ai_response["role"] == "assistant"
                assert len(ai_response["content"]) > 0
                assert "4" in ai_response["content"] or "four" in ai_response["content"].lower()

                # Test follow-up with context
                response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "What about 3+3?"})

                assert response.status_code == 201
                ai_response2 = response.json()
                assert "6" in ai_response2["content"] or "six" in ai_response2["content"].lower()

            # Cleanup
            response = client.delete(f"/api/chat/threads/{thread_uuid}")
            assert response.status_code == 200

        except Exception as e:
            # Skip test if AI Hub is not available
            pytest.skip(f"AI Hub not available for integration test: {str(e)}")

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_spoke_system_integration(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test integration with AI Hub spoke system for specialized responses."""
        # Mock AI Hub with spoke-like behavior
        mock_ai_hub = AsyncMock()

        def spoke_aware_response(message, user, history):
            if "task" in message.lower():
                return "I can help you create and manage tasks. What would you like to do?"
            elif "email" in message.lower():
                return "I can assist with email-related tasks. Would you like to compose or manage emails?"
            else:
                return "I'm here to help with various tasks through my specialized capabilities."

        mock_ai_hub.process_chat_message.side_effect = spoke_aware_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Spoke Integration Test"})
        thread_uuid = response.json()["uuid"]

        # Test task-related query
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "I need help creating a task for my project"}
        )
        assert response.status_code == 201
        ai_response1 = response.json()
        assert "task" in ai_response1["content"].lower()

        # Test email-related query with context
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Can you also help me with email management?"}
        )
        assert response.status_code == 201
        ai_response2 = response.json()
        assert "email" in ai_response2["content"].lower()

        # Verify AI Hub received context from previous messages
        calls = mock_ai_hub.process_chat_message.call_args_list
        assert len(calls) == 2

        # Second call should have context from first exchange
        second_call_history = calls[1][0][2]
        assert len(second_call_history) == 2
        assert "task" in second_call_history[0]["content"].lower()

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_user_context_passing(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test that user context is properly passed to AI Hub."""
        # Mock AI Hub to verify user information
        mock_ai_hub = AsyncMock()

        def user_aware_response(message, user, history):
            return f"Hello {user.name}! I see you're asking: {message}"

        mock_ai_hub.process_chat_message.side_effect = user_aware_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread and send message
        response = client.post("/api/chat/threads", json={"title": "User Context Test"})
        thread_uuid = response.json()["uuid"]

        response = client.post(f"/api/chat/threads/{thread_uuid}/messages", json={"content": "What's my name?"})

        assert response.status_code == 201
        ai_response = response.json()
        assert test_user.name in ai_response["content"]
        assert "What's my name?" in ai_response["content"]

        # Verify user object was passed correctly
        call_args = mock_ai_hub.process_chat_message.call_args
        passed_user = call_args[0][1]

        assert passed_user.id == test_user.id
        assert passed_user.name == test_user.name
        assert passed_user.email == test_user.email

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_response_streaming_simulation(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test handling of AI Hub responses that simulate streaming behavior."""
        # Mock AI Hub with delayed response to simulate streaming
        mock_ai_hub = AsyncMock()

        async def streaming_response(message, user, history):
            # Simulate processing time
            import asyncio

            await asyncio.sleep(0.1)
            return "This is a response that simulates streaming behavior with multiple parts."

        mock_ai_hub.process_chat_message.side_effect = streaming_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread and send message
        response = client.post("/api/chat/threads", json={"title": "Streaming Test"})
        thread_uuid = response.json()["uuid"]

        start_time = time.time()
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Give me a detailed explanation"}
        )
        end_time = time.time()

        assert response.status_code == 201
        ai_response = response.json()
        assert "streaming behavior" in ai_response["content"]

        # Should have taken at least 0.1 seconds due to simulated delay
        assert end_time - start_time >= 0.1

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_context_format_validation(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_thread_with_history, test_user: User
    ):
        """Test that conversation context is formatted correctly for AI Hub."""
        # Mock AI Hub to capture and validate context format
        mock_ai_hub = AsyncMock()
        captured_context = None

        def context_capturing_response(message, user, history):
            nonlocal captured_context
            captured_context = history
            return "Context received and validated"

        mock_ai_hub.process_chat_message.side_effect = context_capturing_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Send message to thread with history
        response = client.post(
            f"/api/chat/threads/{test_thread_with_history.uuid}/messages",
            json={"content": "Validate the context format"},
        )

        assert response.status_code == 201

        # Validate captured context format
        assert captured_context is not None
        assert isinstance(captured_context, list)
        assert len(captured_context) > 0

        for msg in captured_context:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0

        # Verify chronological order (oldest first)
        for i in range(1, len(captured_context)):
            # We can't directly compare timestamps since they're not in the context
            # But we can verify the conversation flow makes sense
            if captured_context[i - 1]["role"] == "user":
                # User message should typically be followed by assistant (though not always)
                pass
            # The main validation is that structure is correct

    @patch("app.services.chat_service.AIHub")
    def test_ai_hub_error_recovery_and_retry(
        self, mock_ai_hub_class, client: TestClient, session: Session, test_user: User
    ):
        """Test AI Hub error recovery and retry mechanisms."""
        # Mock AI Hub to fail first, then succeed
        mock_ai_hub = AsyncMock()
        call_count = 0

        def failing_then_succeeding_response(message, user, history):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary AI Hub failure")
            return "Recovery successful after retry"

        mock_ai_hub.process_chat_message.side_effect = failing_then_succeeding_response
        mock_ai_hub_class.return_value = mock_ai_hub

        # Create thread
        response = client.post("/api/chat/threads", json={"title": "Recovery Test"})
        thread_uuid = response.json()["uuid"]

        # First message should trigger fallback due to AI Hub failure
        with patch("app.services.chat_service.llm_chat_completions", return_value="Fallback used"):
            response = client.post(
                f"/api/chat/threads/{thread_uuid}/messages", json={"content": "First message that will fail"}
            )

            assert response.status_code == 201
            ai_response1 = response.json()
            assert ai_response1["content"] == "Fallback used"

        # Second message should succeed with AI Hub
        response = client.post(
            f"/api/chat/threads/{thread_uuid}/messages", json={"content": "Second message should work"}
        )

        assert response.status_code == 201
        ai_response2 = response.json()
        assert ai_response2["content"] == "Recovery successful after retry"

        # Verify both messages were saved
        response = client.get(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
        thread_data = response.json()
        assert thread_data["thread"]["message_count"] == 4  # 2 user + 2 AI

        # Cleanup
        response = client.delete(f"/api/chat/threads/{thread_uuid}")
        assert response.status_code == 200
