"use client";

import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useMessages } from "../../hooks/useMessages";
import { cn } from "../../lib/utils";
import { Alert, AlertDescription } from "../ui/alert";
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
  width: "w-full sm:w-96",
  height: "h-full sm:h-[600px]",
  position: "inset-0 sm:bottom-6 sm:right-6 sm:top-auto sm:left-auto",
  animation: {
    enter: "animate-in slide-in-from-bottom duration-300 sm:slide-in-from-bottom-2 sm:slide-in-from-right-2",
    exit: "animate-out slide-out-to-bottom duration-200 sm:slide-out-to-bottom-2 sm:slide-out-to-right-2",
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
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
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
          "bg-background border-0 sm:border sm:rounded-2xl shadow-2xl",
          "flex flex-col",
          isOpen ? CHAT_MODAL_CONFIG.animation.enter : CHAT_MODAL_CONFIG.animation.exit
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="chat-title"
      >
        {/* Header */}
        <header className="flex items-center justify-between p-4 sm:p-4 py-4 border-b rounded-t-none sm:rounded-t-2xl bg-background">
          <h2
            id="chat-title"
            className="text-lg font-semibold text-foreground"
          >
            {EMPTY_STATE_MESSAGES.title}
          </h2>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="h-10 w-10 sm:h-8 sm:w-8"
            aria-label="チャットを閉じる"
          >
            <X size={20} className="sm:size-4" />
          </Button>
        </header>

        {/* Content */}
        <div className="flex flex-col flex-1 min-h-0">
          {/* Error Display */}
          {error && (
            <div className="p-4">
              <Alert variant="destructive">
                <AlertDescription>
                  <span className="font-bold">{EMPTY_STATE_MESSAGES.errorTitle}: </span>
                  {error}
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 min-h-0 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="px-4">
                {messages.length === 0 && !isLoading ? (
                  <div className="flex flex-col items-center justify-center text-center text-muted-foreground py-8 min-h-[300px]">
                    <h3 className="text-xl font-bold text-foreground mb-2">
                      {EMPTY_STATE_MESSAGES.title}
                    </h3>
                    <p className="text-sm">{EMPTY_STATE_MESSAGES.description}</p>
                  </div>
                ) : (
                  <div className="space-y-4 py-4 pb-6">
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

          <Separator />

          {/* Input Area */}
          <div className="p-4 sm:p-4 pb-6 sm:pb-4">
            <AIChatInput onSendMessage={sendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </>
  );
}
