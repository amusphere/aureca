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
  width: "w-96",
  height: "h-[600px]",
  position: "bottom-6 right-6",
  animation: {
    enter: "animate-in slide-in-from-bottom-2 slide-in-from-right-2 duration-300",
    exit: "animate-out slide-out-to-bottom-2 slide-out-to-right-2 duration-200",
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
          "bg-background border rounded-2xl shadow-2xl",
          "flex flex-col",
          isOpen ? CHAT_MODAL_CONFIG.animation.enter : CHAT_MODAL_CONFIG.animation.exit
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="chat-title"
      >
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b rounded-t-2xl">
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
            className="h-8 w-8"
            aria-label="チャットを閉じる"
          >
            <X size={16} />
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
          <ScrollArea className="flex-1 px-4">
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground py-8">
                <h3 className="text-xl font-bold text-foreground mb-2">
                  {EMPTY_STATE_MESSAGES.title}
                </h3>
                <p className="text-sm">{EMPTY_STATE_MESSAGES.description}</p>
              </div>
            ) : (
              <div className="space-y-4 py-4">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </ScrollArea>

          <Separator />

          {/* Input Area */}
          <div className="p-4">
            <AIChatInput onSendMessage={sendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </>
  );
}
