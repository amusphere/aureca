"use client";

import { AIChatUsage, AIChatUsageError, AIChatUsageErrorCode, AIChatUsageUtils } from "@/types/AIChatUsage";
import { Send } from "lucide-react";
import { useState } from "react";
import { cn } from "../../lib/utils";
import { LoadingSpinner } from "../commons/LoadingSpinner";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

interface AIChatInputProps {
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  // Usage limit props
  usage?: AIChatUsage | null;
  usageError?: AIChatUsageError | null;
}

export default function AIChatInput({
  onSendMessage,
  isLoading,
  disabled = false,
  placeholder = "メッセージを入力してください...",
  className,
  usage,
  usageError
}: AIChatInputProps) {
  const [message, setMessage] = useState("");

  // Determine if usage limits should disable the input
  const isUsageLimited = usageError !== null || (usage && !usage.canUseChat);
  const isInputDisabled = disabled || isUsageLimited;

  // Generate appropriate placeholder text based on usage status
  const getPlaceholderText = (): string => {
    if (usageError) {
      return AIChatUsageUtils.getErrorMessage(usageError.errorCode as AIChatUsageErrorCode, 'placeholder');
    }

    if (usage && !usage.canUseChat) {
      return "利用制限により現在ご利用いただけません。";
    }

    return placeholder;
  };

  const effectivePlaceholder = getPlaceholderText();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading || isInputDisabled) return;

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

  const canSend = message.trim().length > 0 && !isLoading && !isInputDisabled;

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-4", className)}>
      <div className="relative">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={effectivePlaceholder}
          className={cn(
            "min-h-[88px] max-h-[140px] resize-none w-full",
            "text-base leading-relaxed",
            "border-border/50 focus:border-primary/50",
            "bg-background/80 backdrop-blur-sm",
            "rounded-2xl px-4 py-3",
            "transition-all duration-200",
            "focus:shadow-md focus:shadow-primary/10",
            "placeholder:text-muted-foreground/70",
            isInputDisabled && "opacity-50 cursor-not-allowed",
            // Special styling for usage limit errors
            isUsageLimited && "border-destructive/30 bg-destructive/5"
          )}
          disabled={isLoading || isInputDisabled}
          rows={2}
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          {!isInputDisabled && (
            <p className="text-xs text-muted-foreground/80 hidden sm:block font-medium">
              Shift+Enter で送信
            </p>
          )}
        </div>
      </div>
      <div className="flex justify-between items-center">
        <div className="text-xs text-muted-foreground/60">
          {message.length > 0 && (
            <span className="font-medium">{message.length} 文字</span>
          )}
        </div>
        <Button
          type="submit"
          disabled={!canSend}
          className={cn(
            "h-11 px-6",
            "bg-primary hover:bg-primary/90 disabled:opacity-40",
            "text-primary-foreground font-semibold",
            "rounded-full shadow-lg hover:shadow-xl",
            "transition-all duration-200 ease-out",
            "flex items-center gap-2.5",
            "hover:scale-105 active:scale-95",
            "disabled:hover:scale-100",
            // モバイルでのタッチターゲットサイズを確保
            "min-w-[48px] min-h-[48px]",
            isInputDisabled && "cursor-not-allowed"
          )}
          aria-label={
            isUsageLimited
              ? "利用制限により送信できません"
              : isInputDisabled
                ? "送信できません"
                : "メッセージを送信"
          }
        >
          {isLoading ? (
            <>
              <LoadingSpinner size="sm" variant="minimal" color="secondary" />
              <span className="hidden sm:inline">送信中...</span>
            </>
          ) : (
            <>
              <Send size={16} className="transition-transform duration-200" />
              <span className="hidden sm:inline">
                {isUsageLimited ? "制限中" : isInputDisabled ? "無効" : "送信"}
              </span>
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
