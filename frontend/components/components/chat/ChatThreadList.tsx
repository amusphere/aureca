"use client";

import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { useCallback } from "react";
import type { ChatThread } from "../../../types/Chat";
import { cn } from "../../lib/utils";
import { EmptyState } from "../commons/EmptyState";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";

interface ChatThreadListProps {
  threads: ChatThread[];
  activeThreadUuid: string | null;
  loading: boolean;
  error: string | null;
  onThreadSelect: (threadUuid: string) => void;
  onCreateThread: () => void;
  onDeleteThread?: (threadUuid: string) => void;
  className?: string;
}

/**
 * チャットスレッド一覧表示コンポーネント
 *
 * 要件4.2: スレッド一覧の表示機能
 * 要件4.3: スレッド選択とアクティブ状態管理
 */
export function ChatThreadList({
  threads,
  activeThreadUuid,
  loading,
  error,
  onThreadSelect,
  onCreateThread,
  onDeleteThread,
  className,
}: ChatThreadListProps) {
  // Format thread title with fallback
  const formatThreadTitle = useCallback((thread: ChatThread): string => {
    if (thread.title) {
      return thread.title;
    }

    // Generate fallback title based on creation date
    const createdDate = new Date(thread.created_at * 1000);
    return `チャット ${createdDate.toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })}`;
  }, []);

  // Format relative time
  const formatRelativeTime = useCallback((timestamp: number): string => {
    try {
      return formatDistanceToNow(new Date(timestamp * 1000), {
        addSuffix: true,
        locale: ja,
      });
    } catch {
      return '不明';
    }
  }, []);

  // Handle thread selection
  const handleThreadClick = useCallback((threadUuid: string) => {
    onThreadSelect(threadUuid);
  }, [onThreadSelect]);

  // Handle create thread
  const handleCreateThread = useCallback(() => {
    onCreateThread();
  }, [onCreateThread]);

  if (error) {
    return (
      <div className={cn("p-4", className)}>
        <ErrorDisplay
          error={error}
          variant="compact"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header with Create Button */}
      <div className="flex items-center justify-between p-4 border-b border-border/30">
        <h3 className="text-lg font-semibold text-foreground">
          チャット履歴
        </h3>
        <Button
          onClick={handleCreateThread}
          size="sm"
          variant="outline"
          className="h-8 px-3"
          disabled={loading}
        >
          <Plus className="h-4 w-4 mr-1" />
          新規
        </Button>
      </div>

      {/* Thread List */}
      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full">
          {loading && threads.length === 0 ? (
            <div className="p-4 space-y-3">
              {/* Loading skeleton */}
              {Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg border border-border/30 animate-pulse"
                >
                  <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-3 bg-muted rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : threads.length === 0 ? (
            <div className="p-4">
              <EmptyState
                type="no-data"
                title="チャット履歴がありません"
                description="新しいチャットを開始してください"
                size="sm"
                showIcon={true}
                className="min-h-[200px]"
              />
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {threads.map((thread) => (
                <ThreadListItem
                  key={thread.uuid}
                  thread={thread}
                  isActive={thread.uuid === activeThreadUuid}
                  title={formatThreadTitle(thread)}
                  relativeTime={formatRelativeTime(thread.updated_at)}
                  onClick={() => handleThreadClick(thread.uuid)}
                  onDelete={onDeleteThread ? () => onDeleteThread(thread.uuid) : undefined}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}

interface ThreadListItemProps {
  thread: ChatThread;
  isActive: boolean;
  title: string;
  relativeTime: string;
  onClick: () => void;
  onDelete?: () => void;
}

/**
 * 個別スレッドアイテムコンポーネント
 */
function ThreadListItem({
  thread,
  isActive,
  title,
  relativeTime,
  onClick,
  onDelete,
}: ThreadListItemProps) {
  return (
    <div
      className={cn(
        "group relative p-3 rounded-lg border cursor-pointer transition-all duration-200",
        "hover:bg-muted/50 hover:border-border/60",
        isActive
          ? "bg-primary/10 border-primary/30 shadow-sm"
          : "bg-background border-border/30"
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label={`チャットスレッド: ${title}`}
    >
      {/* Active indicator */}
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full" />
      )}

      <div className="flex items-start gap-3">
        {/* Thread icon */}
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5",
          isActive ? "bg-primary/20" : "bg-muted/60"
        )}>
          <MessageSquare className={cn(
            "h-4 w-4",
            isActive ? "text-primary" : "text-muted-foreground"
          )} />
        </div>

        {/* Thread content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={cn(
              "text-sm font-medium truncate",
              isActive ? "text-primary" : "text-foreground"
            )}>
              {title}
            </h4>

            {/* Message count badge */}
            {thread.message_count > 0 && (
              <span className={cn(
                "flex-shrink-0 text-xs px-2 py-0.5 rounded-full",
                isActive
                  ? "bg-primary/20 text-primary"
                  : "bg-muted text-muted-foreground"
              )}>
                {thread.message_count}
              </span>
            )}
          </div>

          {/* Metadata */}
          <div className="flex items-center justify-between mt-1">
            <p className="text-xs text-muted-foreground">
              {relativeTime}
            </p>
          </div>
        </div>
      </div>

      {/* Hover actions */}
      {onDelete && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <Button
            size="icon"
            variant="ghost"
            className="h-6 w-6 hover:bg-destructive/20 hover:text-destructive"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            aria-label="スレッドを削除"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
}