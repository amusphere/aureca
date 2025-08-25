import { useCallback, useEffect, useState } from 'react';
import type { ChatThread, CreateChatThreadRequest } from '../../types/Chat';

interface UseChatThreadsReturn {
  threads: ChatThread[];
  loading: boolean;
  error: string | null;
  createThread: (request?: CreateChatThreadRequest) => Promise<ChatThread | null>;
  deleteThread: (threadUuid: string) => Promise<boolean>;
  refreshThreads: () => Promise<void>;
  clearError: () => void;
}

export function useChatThreads(): UseChatThreadsReturn {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const fetchThreads = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/chat/threads', {
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
        throw new Error(`スレッドの取得に失敗しました: ${response.status}`);
      }

      const data: ChatThread[] = await response.json();
      setThreads(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'スレッドの取得中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to fetch chat threads:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createThread = useCallback(async (request?: CreateChatThreadRequest): Promise<ChatThread | null> => {
    setError(null);

    try {
      const response = await fetch('/api/chat/threads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request || {}),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('認証が必要です');
        }
        if (response.status === 403) {
          throw new Error('アクセス権限がありません');
        }
        if (response.status === 422) {
          const errorData = await response.json();
          throw new Error(`入力データが無効です: ${errorData.detail || 'バリデーションエラー'}`);
        }
        throw new Error(`スレッドの作成に失敗しました: ${response.status}`);
      }

      const newThread: ChatThread = await response.json();

      // Add the new thread to the beginning of the list
      setThreads(prev => [newThread, ...prev]);

      return newThread;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'スレッドの作成中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to create chat thread:', err);
      return null;
    }
  }, []);

  const deleteThread = useCallback(async (threadUuid: string): Promise<boolean> => {
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
        throw new Error(`スレッドの削除に失敗しました: ${response.status}`);
      }

      // Remove the thread from the list
      setThreads(prev => prev.filter(thread => thread.uuid !== threadUuid));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'スレッドの削除中にエラーが発生しました';
      setError(errorMessage);
      console.error('Failed to delete chat thread:', err);
      return false;
    }
  }, []);

  const refreshThreads = useCallback(async () => {
    await fetchThreads();
  }, [fetchThreads]);

  // Load threads on mount
  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  return {
    threads,
    loading,
    error,
    createThread,
    deleteThread,
    refreshThreads,
    clearError,
  };
}