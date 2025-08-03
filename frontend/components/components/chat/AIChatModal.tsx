"use client";

import { AIChatUsageErrorCode, AIChatUsageUtils } from "@/types/AIChatUsage";
import { AlertCircle, RefreshCw, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useAIChatUsage } from "../../hooks/useAIChatUsage";
import { useMessages } from "../../hooks/useMessages";
import { cn } from "../../lib/utils";
import { EmptyState } from "../commons/EmptyState";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { Separator } from "../ui/separator";
import AIChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";

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
  const { messages, isLoading, error, sendMessage } = useMessages();
  const {
    usage,
    loading: usageLoading,
    error: usageError,
    canUseChat,
    isUsageExhausted,
    refreshUsage,
    incrementUsage,
    clearError: clearUsageError
  } = useAIChatUsage();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Enhanced message sending with usage tracking
  const handleSendMessage = async (message: string) => {
    // Check if user can use chat before sending
    if (!canUseChat) {
      return;
    }

    try {
      // Send the message
      await sendMessage(message);

      // Increment usage count after successful message
      await incrementUsage();
    } catch (error) {
      // Error handling is managed by useMessages hook
      console.error('Failed to send message:', error);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

            {/* Usage Display - Desktop */}
            {usage && (
              <div className="hidden sm:flex items-center gap-2 ml-auto mr-4">
                <Badge
                  variant={canUseChat ? "default" : "destructive"}
                  className={`text-xs font-medium ${AIChatUsageUtils.getUsageStatusColor(usage.remainingCount, usage.dailyLimit)}`}
                >
                  {AIChatUsageUtils.formatUsageDisplay(usage.remainingCount, usage.dailyLimit)}
                </Badge>
                {usageLoading && (
                  <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
                )}
              </div>
            )}
          </div>

          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="h-9 w-9 hover:bg-muted/50 transition-colors duration-200 flex-shrink-0"
            aria-label="チャットを閉じる"
          >
            <X size={18} />
          </Button>
        </header>

        {/* Mobile Usage Display */}
        {usage && (
          <div className="sm:hidden px-6 py-3 bg-muted/30 border-b border-border/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">
                  残り利用回数:
                </span>
                <Badge
                  variant={canUseChat ? "default" : "destructive"}
                  className={`text-xs ${AIChatUsageUtils.getUsageStatusColor(usage.remainingCount, usage.dailyLimit)}`}
                >
                  {AIChatUsageUtils.formatUsageDisplay(usage.remainingCount, usage.dailyLimit)}
                </Badge>
              </div>
              {usageLoading && (
                <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
              )}
            </div>
            {usage.resetTime && (
              <div className="mt-2 text-xs text-muted-foreground/70">
                リセット: {AIChatUsageUtils.getTimeUntilReset(usage.resetTime)}後
              </div>
            )}
          </div>
        )}

        {/* Content */}
        <div className="flex flex-col flex-1 min-h-0">
          {/* Usage Error Display */}
          {usageError && (
            <div className="p-4 bg-destructive/5 border-b border-destructive/20">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-destructive">
                    {AIChatUsageUtils.getErrorTitle(usageError.errorCode as AIChatUsageErrorCode)}
                  </p>
                  <p className="text-xs text-destructive/90 mt-1">
                    {AIChatUsageUtils.getErrorMessage(usageError.errorCode as AIChatUsageErrorCode, 'detailed')}
                  </p>
                  {usageError.resetTime && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs text-destructive/80">
                        リセット時刻: {AIChatUsageUtils.formatResetTime(usageError.resetTime)}
                      </p>
                      <p className="text-xs text-destructive/70">
                        ({AIChatUsageUtils.getTimeUntilReset(usageError.resetTime)}にリセット)
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
                    >
                      <RefreshCw className="h-3 w-3 mr-1" />
                      再確認
                    </Button>
                    {AIChatUsageUtils.getErrorActionText(usageError.errorCode as AIChatUsageErrorCode) &&
                      AIChatUsageUtils.isRecoverableError(usageError.errorCode as AIChatUsageErrorCode) && (
                        <Button
                          size="sm"
                          variant="default"
                          className="h-7 text-xs"
                          onClick={() => {
                            // TODO: Implement plan upgrade navigation
                            console.log('Navigate to plan upgrade');
                          }}
                        >
                          {AIChatUsageUtils.getErrorActionText(usageError.errorCode as AIChatUsageErrorCode)}
                        </Button>
                      )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* System Error Display */}
          {error && (
            <div className="p-4">
              <ErrorDisplay
                error={error}
                variant="compact"
                onRetry={() => window.location.reload()}
              />
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 min-h-0 overflow-hidden bg-gradient-to-b from-background/50 to-background/80">
            <ScrollArea className="h-full">
              <div className="px-6 py-2">
                {messages.length === 0 && !isLoading ? (
                  <EmptyState
                    type="no-data"
                    title={EMPTY_STATE_MESSAGES.title}
                    description={EMPTY_STATE_MESSAGES.description}
                    size="sm"
                    showIcon={false}
                    className="min-h-[320px] flex items-center justify-center"
                  />
                ) : (
                  <div className="space-y-6 py-6">
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        message={message}
                      />
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          <Separator className="bg-border/20" />

          {/* Input Area */}
          <div className="px-6 py-5 bg-background/90 backdrop-blur-sm border-t border-border/10">
            {/* Usage Exhausted Message */}
            {isUsageExhausted && !usageError && (
              <div className="mb-4 p-3 bg-muted/50 border border-border/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground font-medium">
                    本日の利用回数上限に達しました
                  </p>
                </div>
                {usage?.resetTime && (
                  <div className="mt-2 ml-6 space-y-1">
                    <p className="text-xs text-muted-foreground/80">
                      リセット時刻: {AIChatUsageUtils.formatResetTime(usage.resetTime)}
                    </p>
                    <p className="text-xs text-muted-foreground/70">
                      ({AIChatUsageUtils.getTimeUntilReset(usage.resetTime)}にリセット)
                    </p>
                  </div>
                )}
              </div>
            )}

            <AIChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading || usageLoading}
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
