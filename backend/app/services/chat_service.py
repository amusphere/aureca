"""
Chat service for managing AI chat history and conversations.

This service handles:
- Chat thread management
- Message persistence and retrieval
- AI integration with conversation context
- Thread title auto-generation
"""

import logging

from fastapi import HTTPException
from sqlmodel import Session

from app.repositories import chat_message, chat_thread
from app.schema import ChatMessage, ChatThread, User
from app.services.ai import AIHub
from app.utils.llm import llm_chat_completions


class ChatService:
    """Service for managing chat threads and AI conversations with history"""

    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def get_or_create_default_thread(self, user_id: int) -> ChatThread:
        """
        Get user's most recent thread or create a new one if none exists.

        Args:
            user_id: User ID

        Returns:
            ChatThread: The default thread for the user
        """
        try:
            # Get user's most recent thread
            threads = await chat_thread.find_by_user_id(self.session, user_id)

            if threads:
                # Return the most recent thread (already ordered by updated_at desc)
                return threads[0]

            # Create new thread if none exists
            return await chat_thread.create(self.session, user_id, title=None)

        except Exception as e:
            self.logger.error(f"Failed to get or create default thread for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get or create default thread") from e

    async def send_message_with_ai_response(
        self, thread_uuid: str, user_message: str, user: User
    ) -> tuple[ChatMessage, ChatMessage]:
        """
        Send a user message and get AI response with conversation context.

        Args:
            thread_uuid: Thread UUID
            user_message: User's message content
            user: User object

        Returns:
            tuple[ChatMessage, ChatMessage]: User message and AI response
        """
        try:
            # Get thread with permission check
            thread = await chat_thread.find_by_uuid(self.session, thread_uuid, user.id)
            if not thread:
                raise HTTPException(status_code=404, detail="Chat thread not found")

            # Save user message
            user_msg = await chat_message.create(self.session, thread.id, "user", user_message)

            # Get conversation context for AI
            conversation_context = await self.get_conversation_context(thread.id, limit=30)

            # Process with AI Hub
            ai_hub = AIHub(user_id=user.id, session=self.session)

            # Add current message to context
            conversation_context.append({"role": "user", "content": user_message})

            # Get AI response using the hub with conversation history
            ai_response_content = await self._get_ai_response_with_context(conversation_context, ai_hub, user)

            # Save AI response
            ai_msg = await chat_message.create(self.session, thread.id, "assistant", ai_response_content)

            # Update thread timestamp
            await chat_thread.update_timestamp(self.session, thread.id)

            # Auto-generate title if thread doesn't have one and this is the first exchange
            if not thread.title:
                await self._maybe_generate_thread_title(thread.id, user_message)

            return user_msg, ai_msg

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to process message in thread {thread_uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process message") from e

    async def get_conversation_context(self, thread_id: int, limit: int = 30) -> list[dict[str, str]]:
        """
        Get conversation history formatted for AI context.

        Args:
            thread_id: Thread ID
            limit: Maximum number of messages to include

        Returns:
            list[dict[str, str]]: Conversation history in OpenAI format
        """
        try:
            return await chat_message.get_conversation_history_for_ai(self.session, thread_id, limit)
        except Exception as e:
            self.logger.error(f"Failed to get conversation context for thread {thread_id}: {str(e)}")
            return []

    async def generate_thread_title(self, thread_id: int) -> str | None:
        """
        Generate a thread title based on the first user message.

        Args:
            thread_id: Thread ID

        Returns:
            str | None: Generated title or None if generation fails
        """
        try:
            # Get first user message
            first_message = await chat_message.get_first_message_content(self.session, thread_id)
            if not first_message:
                return None

            # Generate title using LLM
            title = await self._generate_title_from_message(first_message)

            if title:
                # Update thread with generated title
                updated_thread = await chat_thread.update_title(self.session, thread_id, title)
                if updated_thread:
                    return title

            return None

        except Exception as e:
            self.logger.error(f"Failed to generate title for thread {thread_id}: {str(e)}")
            return None

    async def _get_ai_response_with_context(
        self, conversation_context: list[dict[str, str]], ai_hub: AIHub, user: User
    ) -> str:
        """
        Get AI response using the hub system with conversation context.

        Args:
            conversation_context: Previous conversation messages
            ai_hub: AI Hub instance
            user: User object

        Returns:
            str: AI response content
        """
        try:
            # Get the current message
            if not conversation_context:
                raise HTTPException(status_code=400, detail="No conversation context provided")

            current_message = conversation_context[-1]["content"]

            # Get conversation history (excluding current message)
            history = conversation_context[:-1] if len(conversation_context) > 1 else []

            # Use the enhanced AI hub with conversation history
            response = await ai_hub.process_chat_message(current_message, user, history)

            # Validate response
            if not response or not isinstance(response, str):
                self.logger.warning("AI hub returned empty or invalid response, using fallback")
                return await self._fallback_ai_response(conversation_context)

            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"AI response generation failed: {str(e)}")
            # Try fallback before raising error
            try:
                return await self._fallback_ai_response(conversation_context)
            except Exception:
                raise HTTPException(status_code=500, detail="AI processing failed") from None

    async def _fallback_ai_response(self, conversation_context: list[dict[str, str]]) -> str:
        """
        Fallback AI response using direct LLM call.

        Args:
            conversation_context: Conversation history

        Returns:
            str: AI response content
        """
        try:
            # Use direct LLM call with conversation context
            # Add system message for chat context
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Respond naturally and helpfully to the user's messages, considering the conversation history.",
                }
            ]
            messages.extend(conversation_context)

            response = llm_chat_completions(prompts=messages, temperature=0.7, max_tokens=1500)

            if not response:
                return "I apologize, but I'm having trouble generating a response right now. Please try again."

            return response

        except Exception as e:
            self.logger.error(f"Fallback AI response failed: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."

    def _format_conversation_for_prompt(self, messages: list[dict[str, str]]) -> str:
        """
        Format conversation history for inclusion in AI prompt.

        Args:
            messages: List of conversation messages

        Returns:
            str: Formatted conversation text
        """
        formatted_lines = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_lines.append(f"{role}: {msg['content']}")

        return "\n".join(formatted_lines)

    async def _maybe_generate_thread_title(self, thread_id: int, first_message: str) -> None:
        """
        Generate thread title if conditions are met.

        Args:
            thread_id: Thread ID
            first_message: First user message content
        """
        try:
            # Only generate title for substantial messages
            if len(first_message.strip()) < 10:
                return

            # Check if this is likely the first real exchange
            message_count = await chat_message.count_by_thread_id(self.session, thread_id)
            if message_count <= 2:  # User message + AI response
                await self.generate_thread_title(thread_id)

        except Exception as e:
            self.logger.error(f"Failed to auto-generate title for thread {thread_id}: {str(e)}")

    async def _generate_title_from_message(self, message_content: str) -> str | None:
        """
        Generate a concise title from the first message using LLM.

        Args:
            message_content: First user message content

        Returns:
            str | None: Generated title or None if generation fails
        """
        try:
            prompt = f"""Based on this user message, generate a short, descriptive title (maximum 50 characters) that summarizes the topic or intent:

Message: "{message_content}"

Generate only the title, nothing else. Make it concise and descriptive."""

            title = llm_chat_completions(
                prompts=[
                    {
                        "role": "system",
                        "content": "You generate concise, descriptive titles for chat conversations. Respond with only the title, no additional text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=50,
            )

            if title:
                # Clean and validate title
                title = title.strip().strip('"').strip("'")
                if len(title) > 50:
                    title = title[:47] + "..."
                return title if title else None

            return None

        except Exception as e:
            self.logger.error(f"Title generation failed: {str(e)}")
            return None

    async def get_thread_with_messages(
        self, thread_uuid: str, user_id: int, page: int = 1, per_page: int = 30
    ) -> tuple[ChatThread, list[ChatMessage], int]:
        """
        Get thread with paginated messages.

        Args:
            thread_uuid: Thread UUID
            user_id: User ID for permission check
            page: Page number
            per_page: Messages per page

        Returns:
            tuple[ChatThread, list[ChatMessage], int]: Thread, messages, total count
        """
        try:
            # Get thread with permission check
            thread = await chat_thread.find_by_uuid(self.session, thread_uuid, user_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Chat thread not found")

            # Get paginated messages
            messages, total_count = await chat_message.find_by_thread_id_paginated(
                self.session, thread.id, page, per_page
            )

            return thread, messages, total_count

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get thread with messages {thread_uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve thread messages") from e

    async def delete_thread(self, thread_uuid: str, user_id: int) -> bool:
        """
        Delete a chat thread and all its messages.

        Args:
            thread_uuid: Thread UUID
            user_id: User ID for permission check

        Returns:
            bool: True if deleted successfully
        """
        try:
            deleted = await chat_thread.delete_by_uuid(self.session, thread_uuid, user_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Chat thread not found")
            return True
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete thread {thread_uuid}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete thread") from e

    async def create_thread(self, user_id: int, title: str | None = None) -> ChatThread:
        """
        Create a new chat thread.

        Args:
            user_id: User ID
            title: Optional thread title

        Returns:
            ChatThread: Created thread
        """
        try:
            return await chat_thread.create(self.session, user_id, title)
        except Exception as e:
            self.logger.error(f"Failed to create thread for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create thread") from e

    async def get_user_threads(self, user_id: int, page: int = 1, per_page: int = 30) -> tuple[list[ChatThread], int]:
        """
        Get user's chat threads with pagination.

        Args:
            user_id: User ID
            page: Page number
            per_page: Threads per page

        Returns:
            tuple[list[ChatThread], int]: Threads and total count
        """
        try:
            return await chat_thread.find_by_user_id_paginated(self.session, user_id, page, per_page)
        except Exception as e:
            self.logger.error(f"Failed to get threads for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user threads") from e
