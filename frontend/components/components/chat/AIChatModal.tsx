"use client";

import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useMessages } from "../../hooks/useMessages";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { Separator } from "../ui/separator";
import { ErrorDisplay } from "../commons/ErrorDisplay";
import { EmptyState } from "../commons/EmptyState";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <h2
              id="chat-title"
              className="text-xl font-semibold text-foreground tracking-tight"
            >
              {EMPTY_STATE_MESSAGES.title}
            </h2>
          </div>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="h-9 w-9 hover:bg-muted/50 transition-colors duration-200"
            aria-label="チャットを閉じる"
          >
            <X size={18} />
          </Button>
        </header>

        {/* Content */}
        <div className="flex flex-col flex-1 min-h-0">
          {/* Error Display */}
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
            <AIChatInput onSendMessage={sendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </>
  );
}
