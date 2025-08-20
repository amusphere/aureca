"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";

interface MessageHistoryLoaderProps {
  hasMoreMessages: boolean;
  loading: boolean;
  onLoadMore: () => void;
  className?: string;
}

export function MessageHistoryLoader({
  hasMoreMessages,
  loading,
  onLoadMore,
  className = ""
}: MessageHistoryLoaderProps) {
  if (!hasMoreMessages && !loading) {
    return null;
  }

  return (
    <div className={`text-center py-4 ${className}`}>
      {loading ? (
        <div className="space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>過去のメッセージを読み込み中...</span>
          </div>
          <div className="space-y-2 px-4">
            {/* Skeleton for loading messages */}
            <div className="flex items-start gap-4">
              <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </div>
            <div className="flex items-start gap-4 justify-end">
              <div className="flex-1 space-y-2 flex flex-col items-end">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-1/3" />
              </div>
              <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
            </div>
          </div>
        </div>
      ) : hasMoreMessages ? (
        <Button
          variant="outline"
          size="sm"
          onClick={onLoadMore}
          className="text-xs hover:bg-muted/50 transition-colors duration-200"
        >
          過去のメッセージを読み込む
        </Button>
      ) : null}
    </div>
  );
}