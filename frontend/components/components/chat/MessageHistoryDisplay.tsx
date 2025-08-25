"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType, PaginationInfo } from "../../../types/Chat";
import { ScrollArea } from "../ui/scroll-area";
import { Skeleton } from "../ui/skeleton";
import ChatMessage from "./ChatMessage";
import { MessageHistoryLoader } from "./MessageHistoryLoader";

interface MessageHistoryDisplayProps {
  messages: ChatMessageType[];
  pagination: PaginationInfo | null;
  loading: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  className?: string;
}

// Convert ChatMessage to legacy Message format for ChatMessage component
const convertToLegacyMessage = (chatMessage: ChatMessageType) => ({
  id: chatMessage.uuid,
  content: chatMessage.content,
  isUser: chatMessage.role === 'user',
  timestamp: new Date(chatMessage.created_at * 1000),
});

export function MessageHistoryDisplay({
  messages,
  pagination,
  loading,
  loadingMore,
  onLoadMore,
  className = ""
}: MessageHistoryDisplayProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added (but not when loading more)
  useEffect(() => {
    if (!loadingMore && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, loadingMore]);

  // Sort messages chronologically (oldest first) to ensure proper display order
  const sortedMessages = [...messages].sort((a, b) => a.created_at - b.created_at);

  if (loading && messages.length === 0) {
    // Initial loading state
    return (
      <div className={`flex-1 min-h-0 overflow-hidden ${className}`}>
        <ScrollArea className="h-full">
          <div className="px-6 py-6 space-y-6">
            {/* Loading skeletons for initial messages */}
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="space-y-4">
                {/* AI message skeleton */}
                <div className="flex items-start gap-4">
                  <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
                  <div className="flex-1 space-y-2 max-w-[75%]">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                </div>
                {/* User message skeleton */}
                <div className="flex items-start gap-4 justify-end">
                  <div className="flex-1 space-y-2 flex flex-col items-end max-w-[75%]">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                  <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    );
  }

  return (
    <div className={`flex-1 min-h-0 overflow-hidden ${className}`}>
      <ScrollArea className="h-full" ref={scrollAreaRef}>
        <div className="px-6 py-2">
          {/* Load More Messages Button/Loader */}
          <MessageHistoryLoader
            hasMoreMessages={pagination?.has_prev ?? false}
            loading={loadingMore}
            onLoadMore={onLoadMore}
          />

          {/* Messages Display */}
          {sortedMessages.length > 0 ? (
            <div className="space-y-6 py-6">
              {sortedMessages.map((message, index) => {
                const prevMessage = index > 0 ? sortedMessages[index - 1] : null;
                const showTimestamp = !prevMessage ||
                  (message.created_at - prevMessage.created_at) > 300; // 5 minutes

                return (
                  <div key={message.uuid} data-testid="chat-message">
                    {/* Timestamp separator for messages with significant time gaps */}
                    {showTimestamp && index > 0 && (
                      <div className="flex items-center justify-center py-2">
                        <div className="text-xs text-muted-foreground bg-muted/50 px-3 py-1 rounded-full">
                          {new Date(message.created_at * 1000).toLocaleString('ja-JP', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                    )}
                    <ChatMessage message={convertToLegacyMessage(message)} />
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="py-6">
              {/* Empty state is handled by parent component */}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}