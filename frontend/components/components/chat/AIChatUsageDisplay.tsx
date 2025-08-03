"use client";

import { AIChatUsage, AIChatUsageError, AIChatUsageErrorCode, AIChatUsageUtils } from "@/types/AIChatUsage";
import { AlertCircle, Clock, RefreshCw } from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

interface AIChatUsageDisplayProps {
  usage: AIChatUsage | null;
  error: AIChatUsageError | null;
  loading?: boolean;
  onRefresh?: () => void;
  onClearError?: () => void;
  variant?: 'compact' | 'detailed';
  className?: string;
}

/**
 * Component for displaying AI Chat usage information with enhanced error handling
 * Implements requirements 4.1, 4.2, 5.1, 5.2, 5.3
 */
export function AIChatUsageDisplay({
  usage,
  error,
  loading = false,
  onRefresh,
  onClearError,
  variant = 'compact',
  className = '',
}: AIChatUsageDisplayProps) {
  // Error state display
  if (error) {
    return (
      <div className={`p-4 bg-destructive/5 border border-destructive/20 rounded-lg ${className}`}>
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-destructive">
              {AIChatUsageUtils.getErrorTitle(error.errorCode as AIChatUsageErrorCode)}
            </p>
            {variant === 'detailed' && (
              <p className="text-xs text-destructive/90 mt-1">
                {AIChatUsageUtils.getErrorMessage(error.errorCode as AIChatUsageErrorCode, 'detailed')}
              </p>
            )}

            {/* Reset time information */}
            {error.resetTime && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center gap-1 text-xs text-destructive/80">
                  <Clock className="h-3 w-3" />
                  <span>リセット時刻: {AIChatUsageUtils.formatResetTime(error.resetTime)}</span>
                </div>
                <p className="text-xs text-destructive/70 ml-4">
                  ({AIChatUsageUtils.getTimeUntilReset(error.resetTime)}にリセット)
                </p>
              </div>
            )}

            {/* Action buttons */}
            {variant === 'detailed' && (
              <div className="flex gap-2 mt-3">
                {onClearError && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onClearError}
                    className="h-7 text-xs"
                  >
                    閉じる
                  </Button>
                )}
                {onRefresh && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onRefresh}
                    disabled={loading}
                    className="h-7 text-xs"
                  >
                    <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    再確認
                  </Button>
                )}
                {AIChatUsageUtils.getErrorActionText(error.errorCode as AIChatUsageErrorCode) &&
                  AIChatUsageUtils.isRecoverableError(error.errorCode as AIChatUsageErrorCode) && (
                    <Button
                      size="sm"
                      variant="default"
                      className="h-7 text-xs"
                      onClick={() => {
                        // TODO: Implement plan upgrade navigation
                        console.log('Navigate to plan upgrade');
                      }}
                    >
                      {AIChatUsageUtils.getErrorActionText(error.errorCode as AIChatUsageErrorCode)}
                    </Button>
                  )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading && !usage) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">利用状況を確認中...</span>
      </div>
    );
  }

  // Usage display
  if (usage) {
    const canUseChat = usage.canUseChat;
    const isExhausted = usage.remainingCount <= 0;

    return (
      <div className={`space-y-2 ${className}`}>
        {/* Usage badge */}
        <div className="flex items-center gap-2">
          <Badge
            variant={canUseChat ? "default" : "destructive"}
            className={`text-xs font-medium ${AIChatUsageUtils.getUsageStatusColor(usage.remainingCount, usage.dailyLimit)}`}
          >
            {AIChatUsageUtils.formatUsageDisplay(usage.remainingCount, usage.dailyLimit)}
          </Badge>
          {loading && (
            <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
          )}
        </div>

        {/* Detailed information */}
        {variant === 'detailed' && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">
              残り利用回数: {usage.remainingCount}回
            </p>
            {usage.resetTime && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground/80">
                <Clock className="h-3 w-3" />
                <span>
                  リセット: {AIChatUsageUtils.getTimeUntilReset(usage.resetTime)}後
                  ({AIChatUsageUtils.formatResetTime(usage.resetTime)})
                </span>
              </div>
            )}
          </div>
        )}

        {/* Exhausted warning */}
        {isExhausted && variant === 'detailed' && (
          <div className="p-2 bg-muted/50 border border-border/30 rounded text-xs text-muted-foreground">
            本日の利用回数上限に達しました。
            {usage.resetTime && (
              <span className="block mt-1">
                {AIChatUsageUtils.getTimeUntilReset(usage.resetTime)}後にリセットされます。
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  // No data state
  return (
    <div className={`text-xs text-muted-foreground ${className}`}>
      利用状況を取得できませんでした
    </div>
  );
}