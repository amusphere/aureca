"use client";

import { MessageCircle } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";

interface FloatingChatButtonProps {
  onClick: () => void;
  hasUnreadMessages?: boolean;
  className?: string;
}

export default function FloatingChatButton({
  onClick,
  hasUnreadMessages = false,
  className
}: FloatingChatButtonProps) {
  return (
    <Button
      onClick={onClick}
      size="icon"
      className={cn(
        "fixed bottom-6 right-6 z-50",
        "h-14 w-14 rounded-full shadow-lg hover:shadow-xl",
        "transition-all duration-200 ease-in-out",
        "bg-primary hover:bg-primary/90",
        "group",
        className
      )}
      aria-label="AIチャットを開く"
    >
      <MessageCircle
        size={24}
        className="transition-transform group-hover:scale-110"
      />
      {hasUnreadMessages && (
        <div className="absolute -top-1 -right-1 h-3 w-3 bg-destructive rounded-full animate-pulse" />
      )}
    </Button>
  );
}
