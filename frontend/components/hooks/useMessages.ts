import { useState } from "react";
import type { AIResponse, Message } from "../../types/chat";
import { useAIChatUsage } from "./useAIChatUsage";
import { AI_CHAT_USAGE_ERROR_MESSAGES } from "@/types/AIChatUsage";

const CHAT_CONSTANTS = {
  completionMessage: "処理が完了しました。",
  apiErrorMessage: "APIエラーが発生しました。",
  fallbackErrorMessage: "予期しないエラーが発生しました。",
} as const;

export function useMessages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Integrate with AI Chat usage limits
  const { usage, canUseChat, error: usageError, refreshUsage } = useAIChatUsage();

  const addMessage = (content: string, isUser: boolean): void => {
    const newMessage: Message = {
      id: `${Date.now()}-${isUser ? 'user' : 'ai'}`,
      content,
      isUser,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const sendMessage = async (messageText: string): Promise<void> => {
    setError(null);
    setIsLoading(true);

    // Check usage limits before sending message
    if (!canUseChat) {
      const errorMessage = usageError?.error || 'AI Chatをご利用いただけません';
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
      setIsLoading(false);
      return;
    }

    // ユーザーのメッセージを追加
    addMessage(messageText, true);

    try {
      const response = await fetch('/api/ai/process', {
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

      const data: AIResponse = await response.json();

      // AIの応答を整形
      const aiResponseText = data.success
        ? (data.summary?.results_text || CHAT_CONSTANTS.completionMessage)
        : (data.error || CHAT_CONSTANTS.apiErrorMessage);

      addMessage(aiResponseText, false);

      // Refresh usage data after successful AI response
      await refreshUsage();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : CHAT_CONSTANTS.fallbackErrorMessage;
      setError(errorMessage);
      addMessage(`エラー: ${errorMessage}`, false);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    // Expose usage information for UI components
    usage,
    canUseChat,
    usageError,
  };
}
