"use client";

import { Loader2, Send } from "lucide-react";
import { useState } from "react";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

interface AIChatInputProps {
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  placeholder?: string;
  className?: string;
}

export default function AIChatInput({
  onSendMessage,
  isLoading,
  placeholder = "メッセージを入力してください...",
  className
}: AIChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const messageToSend = message.trim();
    setMessage("");
    await onSendMessage(messageToSend);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const canSend = message.trim().length > 0 && !isLoading;

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-3", className)}>
      <div className="space-y-2">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="min-h-[80px] max-h-[120px] resize-none w-full text-base"
          disabled={isLoading}
          rows={2}
        />
        <p className="text-xs text-muted-foreground hidden sm:block">
          Shift+Enter で送信
        </p>
      </div>
      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={!canSend}
          className={cn(
            "h-12 px-6",
            "bg-primary hover:bg-primary/90 disabled:opacity-50",
            "text-primary-foreground font-medium",
            "rounded-full shadow-sm",
            "transition-all duration-200 ease-in-out",
            "flex items-center gap-2",
            // モバイルでのタッチターゲットサイズを確保
            "min-w-[48px] min-h-[48px]"
          )}
          aria-label="メッセージを送信"
        >
          {isLoading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span className="hidden sm:inline">送信中...</span>
            </>
          ) : (
            <>
              <Send size={18} />
              <span className="hidden sm:inline">送信</span>
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
