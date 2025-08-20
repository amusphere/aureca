"use client";

import { useCallback, useState } from "react";
import type { ChatThread, CreateChatThreadRequest } from "../../../types/chat";
import { useChatThreads } from "../../hooks/useChatThreads";
import { cn } from "../../lib/utils";
import { ChatThreadActions } from "./ChatThreadActions";
import { ChatThreadList } from "./ChatThreadList";

interface ChatThreadManagerProps {
  activeThreadUuid: string | null;
  onThreadSelect: (threadUuid: string) => void;
  onThreadCreated?: (thread: ChatThread) => void;
  onThreadDeleted?: (threadUuid: string) => void;
  className?: string;
}

/**
 * チャットスレッド管理コンポーネント
 * スレッド一覧表示と操作機能を統合
 *
 * 要件4.1: 新しいスレッド作成機能
 * 要件4.2: スレッド一覧の表示機能
 * 要件4.3: スレッド選択とアクティブ状態管理
 * 要件4.4: スレッド削除機能と確認ダイアログ
 */
export function ChatThreadManager({
  activeThreadUuid,
  onThreadSelect,
  onThreadCreated,
  onThreadDeleted,
  className,
}: ChatThreadManagerProps) {
  const {
    threads,
    loading,
    error,
    createThread,
    deleteThread,
    clearError,
  } = useChatThreads();

  const [actionInProgress, setActionInProgress] = useState(false);

  // Handle thread creation
  const handleCreateThread = useCallback(async (request?: CreateChatThreadRequest): Promise<ChatThread | null> => {
    if (actionInProgress) return null;

    setActionInProgress(true);
    try {
      const newThread = await createThread(request);
      if (newThread && onThreadCreated) {
        onThreadCreated(newThread);
      }
      return newThread;
    } finally {
      setActionInProgress(false);
    }
  }, [createThread, onThreadCreated, actionInProgress]);

  // Handle thread deletion
  const handleDeleteThread = useCallback(async (threadUuid: string): Promise<boolean> => {
    if (actionInProgress) return false;

    setActionInProgress(true);
    try {
      const success = await deleteThread(threadUuid);
      if (success && onThreadDeleted) {
        onThreadDeleted(threadUuid);
      }
      return success;
    } finally {
      setActionInProgress(false);
    }
  }, [deleteThread, onThreadDeleted, actionInProgress]);

  // Handle thread selection
  const handleThreadSelect = useCallback((threadUuid: string) => {
    if (actionInProgress) return;
    onThreadSelect(threadUuid);
  }, [onThreadSelect, actionInProgress]);

  // Enhanced delete handler for individual threads
  const handleDeleteFromList = useCallback((threadUuid: string) => {
    const thread = threads.find(t => t.uuid === threadUuid);
    if (thread) {
      return handleDeleteThread(threadUuid);
    }
    return Promise.resolve(false);
  }, [threads, handleDeleteThread]);

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Thread List */}
      <div className="flex-1 min-h-0">
        <ChatThreadList
          threads={threads}
          activeThreadUuid={activeThreadUuid}
          loading={loading}
          error={error}
          onThreadSelect={handleThreadSelect}
          onCreateThread={() => handleCreateThread()}
          onDeleteThread={handleDeleteFromList}
        />
      </div>

      {/* Action Bar */}
      <div className="border-t border-border/30 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ChatThreadActions
              onCreateThread={handleCreateThread}
              onDeleteThread={handleDeleteThread}
              disabled={loading || actionInProgress}
              className="flex-1"
            />
          </div>

          {/* Thread count */}
          <div className="text-xs text-muted-foreground">
            {threads.length > 0 && (
              <span>
                {threads.length} 件のチャット
              </span>
            )}
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="mt-3 p-2 bg-destructive/5 border border-destructive/20 rounded text-xs text-destructive">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={clearError}
                className="ml-2 hover:underline"
              >
                閉じる
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface CompactThreadManagerProps {
  activeThreadUuid: string | null;
  onThreadSelect: (threadUuid: string) => void;
  maxHeight?: string;
  className?: string;
}

/**
 * コンパクト版スレッド管理コンポーネント
 * モーダルやサイドバーでの使用に適している
 */
export function CompactThreadManager({
  activeThreadUuid,
  onThreadSelect,
  maxHeight = "400px",
  className,
}: CompactThreadManagerProps) {
  const {
    threads,
    loading,
    error,
    createThread,
    deleteThread,
  } = useChatThreads();

  const handleCreateThread = useCallback(async () => {
    const newThread = await createThread();
    if (newThread) {
      onThreadSelect(newThread.uuid);
    }
  }, [createThread, onThreadSelect]);

  const handleDeleteThread = useCallback(async (threadUuid: string) => {
    const success = await deleteThread(threadUuid);
    if (success && threadUuid === activeThreadUuid) {
      // If the active thread was deleted, select the first available thread
      const remainingThreads = threads.filter(t => t.uuid !== threadUuid);
      if (remainingThreads.length > 0) {
        onThreadSelect(remainingThreads[0].uuid);
      }
    }
    return success;
  }, [deleteThread, activeThreadUuid, threads, onThreadSelect]);

  return (
    <div
      className={cn("flex flex-col bg-background border border-border/30 rounded-lg", className)}
      style={{ maxHeight }}
    >
      <ChatThreadList
        threads={threads}
        activeThreadUuid={activeThreadUuid}
        loading={loading}
        error={error}
        onThreadSelect={onThreadSelect}
        onCreateThread={handleCreateThread}
        onDeleteThread={handleDeleteThread}
        className="flex-1"
      />
    </div>
  );
}