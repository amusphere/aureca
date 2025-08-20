"use client";

import { getErrorMessage } from "@/constants/error_messages";
import { AlertCircle, RefreshCw, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAIChatUsage } from "../../hooks/useAIChatUsage";
import { useChatMessages } from "../../hooks/useChatMessages";
import { useChatThreads } from "../../hooks/useChatThreads";
import { cn } from "../../lib/utils";
import { EmptyState } from "../commons/EmptyState";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { Button } from "../ui/button";
import { Separator } from "../ui/separator";
import { UsageDisplay } from "../ui/usage-display";
import AIChatInput from "./ChatInput";
import { MessageHistoryDisplay } from "./MessageHistoryDisplay";

interface AIChatModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CHAT_MODAL_CONFIG = {
  // モバイル: フルスクリーン、デスクトップ: 固定サイズ
  width: "w-full sm:w-[420px]",
  height: "h-full sm:h-[680px]",
  position: "inset-0 sm:bottom-8 sm:right-8 sm:top-auto sm:left-auto",
  animation: {
    enter: "animate-in slide-in-from-bottom duration-300 ease-out sm:slide-in-from-bottom-4 sm:slide-in-from-right-4",
    exit: "animate-out slide-out-to-bottom duration-200 ease-in sm:slide-out-to-bottom-4 sm:slide-out-to-right-4",
  },
} as const;

const EMPTY_STATE_MESSAGES = {
  title: "AIアシスタント",
  description: "何かお手伝いできることはありますか？",
  errorTitle: "エラーが発生しました",
} as const;

export default function AIChatModal({ isOpen, onClose }: AIChatModalProps) {
  const [defaultThreadUuid, setDefaultThreadUuid] = useState<string | null>(null);

  // Chat threads management (for getting/creating default thread)
  const {
    threads,
    loading: threadsLoading,
    error: threadsError,
    createThread,
    refreshThreads
  } = useChatThreads();

  // Messages for default thread
  const {
    messages: chatMessages,
    loading: messagesLoading,
    loadingMore: loadingMoreMessages,
    sendingMessage,
    error: messagesError,
    sendMessage: sendChatMessage,
    loadMoreMessages,
    clearMessages,
    pagination
  } = useChatMessages(defaultThreadUuid);

  // Usage management
  const {
    usage,
    loading: usageLoading,
    error: usageError,
    dailyLimit,
    planName,
    canUseChat,
    isUsageExhausted,
    refreshUsage,
    incrementUsage,
    clearError: clearUsageError
  } = useAIChatUsage();



  // Get or create default thread
  const ensureDefaultThread = async (): Promise<string | null> => {
    if (defaultThreadUuid) {
      return defaultThreadUuid;
    }

    // Check if there's an existing thread
    if (threads.length > 0) {
      const thread = threads[0]; // Use the first thread as default
      setDefaultThreadUuid(thread.uuid);
      return thread.uuid;
    }

    // Create a new thread
    const newThread = await createThread();
    if (newThread) {
      setDefaultThreadUuid(newThread.uuid);
      return newThread.uuid;
    }

    return null;
  };

  // Auto-select default thread
  useEffect(() => {
    if (isOpen && !defaultThreadUuid && threads.length > 0) {
      setDefaultThreadUuid(threads[0].uuid);
    }
  }, [isOpen, defaultThreadUuid, threads]);

  // Clear chat history with confirmation
  const handleClearHistory = async () => {
    if (confirm('チャット履歴をクリアしますか？この操作は取り消せません。')) {
      const success = await clearMessages();
      if (success) {
        // After clearing, we need to create a new thread for future messages
        setDefaultThreadUuid(null);
      }
    }
  };

  // Enhanced message sending with usage tracking
  const handleSendMessage = async (message: string) => {
    // Check if user can use chat before sending
    if (!canUseChat) {
      return;
    }

    try {
      // Ensure we have a default thread
      const threadUuid = await ensureDefaultThread();
      if (!threadUuid) {
        throw new Error('スレッドの作成に失敗しました');
      }

      // Send the message using the new chat system
      await sendChatMessage(message);

      // Increment usage count after successful message
      await incrementUsage();
    } catch (error) {
      // Error handling is managed by useChatMessages hook
      console.error('Failed to send message:', error);
    }
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-md transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Chat Container */}
      <div
        className={cn(
          "fixed z-50",
          CHAT_MODAL_CONFIG.width,
          CHAT_MODAL_CONFIG.height,
          CHAT_MODAL_CONFIG.position,
          "bg-background/95 backdrop-blur-xl border-0 sm:border sm:border-border/50 sm:rounded-3xl",
          "shadow-2xl sm:shadow-[0_32px_64px_-12px_rgba(0,0,0,0.25)]",
          "flex flex-col overflow-hidden",
          isOpen ? CHAT_MODAL_CONFIG.animation.enter : CHAT_MODAL_CONFIG.animation.exit
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="chat-title"
      >
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-5 border-b border-border/30 bg-background/80 backdrop-blur-sm">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className={cn(
              "w-2 h-2 rounded-full transition-colors duration-300",
              canUseChat ? "bg-green-500 animate-pulse" : "bg-red-500"
            )} />
            <h2
              id="chat-title"
              className="text-xl font-semibold text-foreground tracking-tight"
            >
              {EMPTY_STATE_MESSAGES.title}
            </h2>

            {(usageLoading || threadsLoading || messagesLoading || loadingMoreMessages) && (
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground ml-2" aria-label="読み込み中" />
            )}

            {/* Usage Display - Desktop Only (Compact). Hide when error exists to avoid duplicate titles */}
            {!usageError && (
              <div className="hidden sm:flex items-center ml-auto mr-4">
                <UsageDisplay
                  currentUsage={usage ? Math.max(0, (usage.daily_limit ?? dailyLimit ?? 0) - (usage.remaining_count ?? 0)) : 0}
                  dailyLimit={usage?.daily_limit ?? (dailyLimit ?? 0)}
                  planName={planName}
                  resetTime={usage?.reset_time}
                  variant="compact"
                  loading={usageLoading}
                  error={usageError}
                  className="text-xs"
                />
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Clear History Button */}
            {chatMessages.length > 0 && (
              <Button
                onClick={handleClearHistory}
                variant="ghost"
                size="icon"
                className="h-9 w-9 hover:bg-muted/50 transition-colors duration-200"
                aria-label="チャット履歴をクリア"
                title="チャット履歴をクリア"
              >
                <Trash2 size={16} />
              </Button>
            )}

            <Button
              onClick={onClose}
              variant="ghost"
              size="icon"
              className="h-9 w-9 hover:bg-muted/50 transition-colors duration-200 flex-shrink-0"
              aria-label="チャットを閉じる"
            >
              <X size={18} />
            </Button>
          </div>
        </header>

        {/* Mobile Usage Display - Full Width */}
        <div className="sm:hidden">
          <UsageDisplay
            currentUsage={usage ? Math.max(0, (usage.daily_limit ?? dailyLimit ?? 0) - (usage.remaining_count ?? 0)) : 0}
            dailyLimit={usage?.daily_limit ?? (dailyLimit ?? 0)}
            planName={planName}
            resetTime={usage?.reset_time}
            variant="minimal"
            loading={usageLoading}
            error={usageError}
            className="px-6 py-3 bg-muted/30 border-b border-border/20"
          />
        </div>

        {/* Content */}
        <div className="flex flex-col flex-1 min-h-0">
          {/* Usage Error Display - Only show when not handled by UsageDisplay */}
          {usageError && (
            <div className="p-4 bg-destructive/5 border-b border-destructive/20" data-testid="usage-error-display">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-destructive">
                    {getErrorMessage(usageError.error_code, false)}
                  </p>
                  <p className="text-xs text-destructive/90 mt-1">
                    {usageError.error_code === 'USAGE_LIMIT_EXCEEDED'
                      ? '本日のAIChat利用回数が上限に達しています。明日の00:00にリセットされます。'
                      : usageError.error_code === 'PLAN_RESTRICTION'
                        ? '現在のプランではAIChatをご利用いただけません。プランをアップグレードしてご利用ください。'
                        : usageError.error_code === 'SYSTEM_ERROR'
                          ? '一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。'
                          : getErrorMessage(usageError.error_code, true)}
                  </p>
                  {usageError.reset_time && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs text-destructive/80">
                        リセット時刻: {new Date(usageError.reset_time).toLocaleString('ja-JP')}
                      </p>
                      <p className="text-xs text-destructive/70">
                        ({Math.ceil((new Date(usageError.reset_time).getTime() - Date.now()) / (1000 * 60 * 60))}時間後にリセット)
                      </p>
                    </div>
                  )}
                  <div className="flex gap-2 mt-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={clearUsageError}
                      className="h-7 text-xs"
                    >
                      閉じる
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={refreshUsage}
                      className="h-7 text-xs"
                      data-testid="modal-refresh-button"
                    >
                      <RefreshCw className="h-3 w-3 mr-1" />
                      再確認
                    </Button>
                    {getErrorMessage(usageError.error_code, false) === 'プランの制限' && (
                      <Button
                        size="sm"
                        variant="default"
                        className="h-7 text-xs"
                        onClick={() => {
                          // TODO: Implement plan upgrade navigation
                          console.log('Navigate to plan upgrade');
                        }}
                      >
                        プランをアップグレード
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* System Error Display */}
          {(threadsError || messagesError) && (
            <div className="p-4" data-testid="error-display">
              <ErrorDisplay
                error={threadsError || messagesError || ''}
                variant="compact"
                onRetry={() => {
                  if (threadsError) refreshThreads();
                  if (messagesError) window.location.reload();
                }}
              />
            </div>
          )}

          {/* Messages Area */}
          {chatMessages.length === 0 && !messagesLoading ? (
            <div className="flex-1 min-h-0 overflow-hidden bg-gradient-to-b from-background/50 to-background/80 flex items-center justify-center">
              <EmptyState
                type="no-data"
                title={EMPTY_STATE_MESSAGES.title}
                description={EMPTY_STATE_MESSAGES.description}
                size="sm"
                showIcon={false}
                className="min-h-[320px] flex items-center justify-center"
              />
            </div>
          ) : (
            <MessageHistoryDisplay
              messages={chatMessages}
              pagination={pagination}
              loading={messagesLoading}
              loadingMore={loadingMoreMessages}
              onLoadMore={loadMoreMessages}
              className="bg-gradient-to-b from-background/50 to-background/80"
            />
          )}

          <Separator className="bg-border/20" />

          {/* Input Area */}
          <div className="px-6 py-5 bg-background/90 backdrop-blur-sm border-t border-border/10">
            {/* Usage Exhausted Message */}
            {(isUsageExhausted || !!usageError) && (
              <div className="mb-4 p-3 bg-muted/50 border border-border/30 rounded-lg" data-testid="usage-exhausted-message">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground font-medium">
                    本日の利用回数上限に達しました
                  </p>
                </div>
                {usage?.reset_time && (
                  <div className="mt-2 ml-6 space-y-1">
                    <p className="text-xs text-muted-foreground/80">
                      リセット時刻: {new Date(usage.reset_time).toLocaleString('ja-JP')}
                    </p>
                    <p className="text-xs text-muted-foreground/70">
                      ({Math.ceil((new Date(usage.reset_time).getTime() - Date.now()) / (1000 * 60 * 60))}時間後にリセット)
                    </p>
                  </div>
                )}
              </div>
            )}

            <AIChatInput
              onSendMessage={handleSendMessage}
              isLoading={sendingMessage || usageLoading}
              disabled={!canUseChat || isUsageExhausted}
              usage={usage}
              usageError={usageError}
            />
          </div>
        </div>
      </div>
    </>
  );
}
