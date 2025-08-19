import { AI_CHAT_USAGE_ERROR_MESSAGES } from "@/types/AIChatUsage";
import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, Message } from "../../types/chat";
import { useAIChatUsage } from "./useAIChatUsage";
import { useChatMessages } from "./useChatMessages";
import { useChatThreads } from "./useChatThreads";

const CHAT_CONSTANTS = {
  completionMessage: "処理が完了しました。",
  apiErrorMessage: "APIエラーが発生しました。",
  fallbackErrorMessage: "予期しないエラーが発生しました。",
} as const;

// Utility function to convert ChatMessage to legacy Message format
const convertChatMessageToMessage = (chatMessage: ChatMessage): Message => ({
  id: chatMessage.uuid,
  content: chatMessage.content,
  isUser: chatMessage.role === 'user',
  timestamp: new Date(chatMessage.created_at * 1000), // Convert Unix timestamp to Date
});

export function useMessages() {
  const [currentThreadUuid, setCurrentThreadUuid] = useState<string | null>(null);
  const [legacyMessages, setLegacyMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Integrate with AI Chat usage limits
  const { usage, canUseChat, error: usageError, refreshUsage } = useAIChatUsage();

  // Use new chat history hooks
  const { threads, createThread, loading: threadsLoading } = useChatThreads();
  const {
    messages: chatMessages,
    sendMessage: sendChatMessage,
    sendingMessage,
    error: messagesError
  } = useChatMessages(currentThreadUuid);

  // Get or create default thread
  const ensureDefaultThread = useCallback(async (): Promise<string | null> => {
    if (currentThreadUuid) {
      return currentThreadUuid;
    }

    // Check if there's an existing thread
    if (threads.length > 0) {
      const defaultThread = threads[0]; // Use the most recent thread
      setCurrentThreadUuid(defaultThread.uuid);
      return defaultThread.uuid;
    }

    // Create a new thread
    const newThread = await createThread();
    if (newThread) {
      setCurrentThreadUuid(newThread.uuid);
      return newThread.uuid;
    }

    return null;
  }, [currentThreadUuid, threads, createThread]);

  // Convert chat messages to legacy format
  useEffect(() => {
    const convertedMessages = chatMessages.map(convertChatMessageToMessage);
    setLegacyMessages(convertedMessages);
  }, [chatMessages]);

  // Handle errors from chat messages
  useEffect(() => {
    if (messagesError) {
      setError(messagesError);
    }
  }, [messagesError]);

  const addMessage = (content: string, isUser: boolean): void => {
    const newMessage: Message = {
      id: `${Date.now()}-${isUser ? 'user' : 'ai'}`,
      content,
      isUser,
      timestamp: new Date(),
    };
    setLegacyMessages(prev => [...prev, newMessage]);
  };

  const sendMessage = async (messageText: string): Promise<void> => {
    setError(null);

    // Check usage limits before sending message
    if (!canUseChat) {
      const errorMessage = usageError?.error || 'AI Chatをご利用いただけません';
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
      return;
    }

    try {
      // Ensure we have a thread to send the message to
      const threadUuid = await ensureDefaultThread();
      if (!threadUuid) {
        throw new Error('チャットスレッドの作成に失敗しました');
      }

      // Send message using the new chat history system
      const aiResponse = await sendChatMessage(messageText);

      if (aiResponse) {
        // Refresh usage data after successful AI response
        await refreshUsage();
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : CHAT_CONSTANTS.fallbackErrorMessage;
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
    }
  };

  // Legacy API compatibility - use new chat system but maintain old interface
  const sendMessageLegacy = async (messageText: string): Promise<void> => {
    setError(null);

    // Check usage limits before sending message
    if (!canUseChat) {
      const errorMessage = usageError?.error || 'AI Chatをご利用いただけません';
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
      return;
    }

    // Add user message immediately for UI responsiveness
    addMessage(messageText, true);

    try {
      // Use the new chat history endpoint
      const threadUuid = await ensureDefaultThread();
      if (!threadUuid) {
        throw new Error('チャットスレッドの作成に失敗しました');
      }

      const response = await fetch(`/api/ai/chat?thread_uuid=${threadUuid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: messageText }),
      });

      if (!response.ok) {
        // Handle usage limit errors specifically
        if (response.status === 429) {
          const errorData = await response.json();
          const errorMessage = errorData.error || AI_CHAT_USAGE_ERROR_MESSAGES.USAGE_LIMIT_EXCEEDED;
          setError(errorMessage);
          addMessage(`エラー: ${errorMessage}`, false);
          // Refresh usage data to get updated limits
          await refreshUsage();
          return;
        }

        if (response.status === 403) {
          const errorData = await response.json();
          const errorMessage = errorData.error || AI_CHAT_USAGE_ERROR_MESSAGES.PLAN_RESTRICTION;
          setError(errorMessage);
          addMessage(`エラー: ${errorMessage}`, false);
          return;
        }

        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Extract AI response from the new API format
      let aiResponseText = CHAT_CONSTANTS.completionMessage;

      if (data.ai_response) {
        aiResponseText = data.ai_response.summary?.results_text ||
          data.ai_response.error ||
          CHAT_CONSTANTS.completionMessage;
      } else if (data.success === false) {
        aiResponseText = data.error || CHAT_CONSTANTS.apiErrorMessage;
      }

      addMessage(aiResponseText, false);

      // Refresh usage data after successful AI response
      await refreshUsage();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : CHAT_CONSTANTS.fallbackErrorMessage;
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
    }
  };

  return {
    messages: legacyMessages,
    isLoading: sendingMessage || threadsLoading,
    error,
    sendMessage: sendMessage, // Use new chat history system
    sendMessageLegacy, // Fallback for legacy compatibility
    // Expose usage information for UI components
    usage,
    canUseChat,
    usageError,
    // Expose new chat history functionality
    currentThreadUuid,
    setCurrentThreadUuid,
    threads,
  };
}
