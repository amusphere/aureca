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
  placeholder = "メッセージを入力してください... (Shift+Enter で送信)",
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
    <form onSubmit={handleSubmit} className={cn("flex gap-2", className)}>
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="min-h-[44px] max-h-[120px] resize-none flex-1"
        disabled={isLoading}
        rows={1}
      />
      <Button
        type="submit"
        disabled={!canSend}
        size="icon"
        className="h-[44px] w-[44px] shrink-0"
        aria-label="メッセージを送信"
      >
        {isLoading ? (
          <Loader2 size={18} className="animate-spin" />
        ) : (
          <Send size={18} />
        )}
      </Button>
    </form>
  );
}
