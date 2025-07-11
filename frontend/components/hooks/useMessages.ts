import { useState } from "react";
import type { AIResponse, Message } from "../../types/chat";

const CHAT_CONSTANTS = {
  completionMessage: "処理が完了しました。",
  apiErrorMessage: "APIエラーが発生しました。",
  fallbackErrorMessage: "予期しないエラーが発生しました。",
} as const;

export function useMessages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: AIResponse = await response.json();

      // AIの応答を整形
      const aiResponseText = data.success
        ? (data.summary?.results_text || CHAT_CONSTANTS.completionMessage)
        : (data.error || CHAT_CONSTANTS.apiErrorMessage);

      addMessage(aiResponseText, false);

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
  };
}
