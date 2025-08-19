import { useCallback, useEffect, useState } from 'react';
import type {
  ChatMessage,
  ChatThreadWithMessages,
  PaginationInfo,
  SendMessageRequest
} from '../../types/chat';

interface UseChatMessagesReturn {
  messages: ChatMessage[];
  pagination: PaginationInfo | null;
  loading: boolean;
  loadingMore: boolean;
  sendingMessage: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<ChatMessage | null>;
  loadMessages: (page?: number) => Promise<void>;
  loadMoreMessages: () => Promise<void>;
  refreshMessages: () => Promise<void>;
  clearMessages: () => Promise<boolean>;
  clearError: () => void;
}

export function useChatMessages(threadUuid: string | null): UseChatMessagesReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const loadMessages = useCallback(async (page: number = 1) => {
    if (!threadUuid) {
      setMessages([]);
      setPagination(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/chat/threads/${threadUuid}?page=${page}&per_page=30`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('認証が必要です');
        }
        if (response.status === 403) {
          throw new Error('アクセス権限がありません');
        }
        if (response.status === 404) {
          throw new Error('スレッドが見つかりません');
        }
        throw new Error(`メッセージの取得に失敗しました: ${response.status}`);
      }

      const data: ChatThreadWithMessages = await response.json();

      // Sort messages by created_at to ensure chronological order (oldest first)
      const sortedMessages = [...data.messages].sort((a, b) => a.created_at - b.created_at);

      if (page === 1) {
        // First page - replace all messages
        setMessages(sortedMessages);
      } else {
        // Additional pages - prepend older messages to existing messages
        // Since we're loading older messages, they should come before current messages
        setMessages(prev => [...sortedMessages, ...prev]);
      }

      setPagination(data.pagination);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'メッセージの取得中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to load chat messages:', err);
    } finally {
      setLoading(false);
    }
  }, [threadUuid]);

  const loadMoreMessages = useCallback(async () => {
    if (!pagination?.has_prev || loading || loadingMore) {
      return;
    }

    setLoadingMore(true);
    setError(null);

    try {
      const response = await fetch(`/api/chat/threads/${threadUuid}?page=${pagination.page + 1}&per_page=30`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('認証が必要です');
        }
        if (response.status === 403) {
          throw new Error('アクセス権限がありません');
        }
        if (response.status === 404) {
          throw new Error('スレッドが見つかりません');
        }
        throw new Error(`メッセージの取得に失敗しました: ${response.status}`);
      }

      const data: ChatThreadWithMessages = await response.json();

      // Sort messages by created_at to ensure chronological order (oldest first)
      const sortedMessages = [...data.messages].sort((a, b) => a.created_at - b.created_at);

      // Prepend older messages to existing messages
      setMessages(prev => [...sortedMessages, ...prev]);
      setPagination(data.pagination);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '過去のメッセージの取得中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to load more messages:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [pagination, loading, loadingMore, threadUuid]);

  const sendMessage = useCallback(async (content: string): Promise<ChatMessage | null> => {
    if (!threadUuid) {
      setError('スレッドが選択されていません');
      return null;
    }

    setSendingMessage(true);
    setError(null);

    try {
      const request: SendMessageRequest = { content };

      const response = await fetch(`/api/chat/threads/${threadUuid}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('認証が必要です');
        }
        if (response.status === 403) {
          throw new Error('アクセス権限がありません');
        }
        if (response.status === 404) {
          throw new Error('スレッドが見つかりません');
        }
        if (response.status === 422) {
          const errorData = await response.json();
          throw new Error(`入力データが無効です: ${errorData.detail || 'バリデーションエラー'}`);
        }
        if (response.status === 429) {
          throw new Error('利用回数の上限に達しました');
        }
        throw new Error(`メッセージの送信に失敗しました: ${response.status}`);
      }

      const aiResponse: ChatMessage = await response.json();

      // Add both user message and AI response to the messages list
      // The API should return the AI response, and we need to create the user message
      const userMessage: ChatMessage = {
        uuid: `temp-${Date.now()}`, // Temporary UUID for user message
        role: 'user',
        content,
        created_at: Date.now() / 1000, // Convert to Unix timestamp
      };

      // Add messages in chronological order
      setMessages(prev => [...prev, userMessage, aiResponse]);

      // Update pagination info if available
      if (pagination) {
        setPagination(prev => prev ? {
          ...prev,
          total_messages: prev.total_messages + 2, // User + AI message
        } : null);
      }

      return aiResponse;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'メッセージの送信中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to send message:', err);
      return null;
    } finally {
      setSendingMessage(false);
    }
  }, [threadUuid, pagination]);

  const refreshMessages = useCallback(async () => {
    await loadMessages(1);
  }, [loadMessages]);

  const clearMessages = useCallback(async (): Promise<boolean> => {
    if (!threadUuid) {
      setError('スレッドが選択されていません');
      return false;
    }

    setError(null);

    try {
      const response = await fetch(`/api/chat/threads/${threadUuid}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('認証が必要です');
        }
        if (response.status === 403) {
          throw new Error('アクセス権限がありません');
        }
        if (response.status === 404) {
          throw new Error('スレッドが見つかりません');
        }
        throw new Error(`履歴のクリアに失敗しました: ${response.status}`);
      }

      // Clear local messages
      setMessages([]);
      setPagination(null);

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴のクリア中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to clear chat messages:', err);
      return false;
    }
  }, [threadUuid]);

  // Load messages when thread changes
  useEffect(() => {
    if (threadUuid) {
      loadMessages(1);
    } else {
      setMessages([]);
      setPagination(null);
    }
  }, [threadUuid, loadMessages]);

  return {
    messages,
    pagination,
    loading,
    loadingMore,
    sendingMessage,
    error,
    sendMessage,
    loadMessages,
    loadMoreMessages,
    refreshMessages,
    clearMessages,
    clearError,
  };
}