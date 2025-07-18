"use client";

import { Button } from "@/components/components/ui/button";
import { cn } from "@/components/lib/utils";
import { AlertCircle, AlertTriangle, RefreshCw, Server, WifiOff, X } from "lucide-react";
import { ErrorState } from "../../hooks/useErrorHandling";

interface ErrorDisplayProps {
  error: ErrorState | string;
  onDismiss?: () => void;
  onRetry?: () => void;
  className?: string;
  variant?: "default" | "compact" | "inline";
}

/**
 * Enhanced error display component with modern styling and improved visual hierarchy
 */
export function ErrorDisplay({
  error,
  onDismiss,
  onRetry,
  className,
  variant = "default"
}: ErrorDisplayProps) {
  const errorState = typeof error === 'string'
    ? { message: error, type: 'unknown' as const, retryable: true }
    : error;

  const getErrorConfig = (type: ErrorState['type']) => {
    switch (type) {
      case 'network':
        return {
          title: 'ネットワークエラー',
          icon: WifiOff,
          description: '接続に問題が発生しました。インターネット接続を確認してください。',
          bgColor: 'bg-red-50 dark:bg-red-950/20',
          borderColor: 'border-red-200 dark:border-red-800',
          iconColor: 'text-red-500',
          titleColor: 'text-red-800 dark:text-red-200'
        };
      case 'validation':
        return {
          title: '入力エラー',
          icon: AlertTriangle,
          description: '入力内容に問題があります。',
          bgColor: 'bg-amber-50 dark:bg-amber-950/20',
          borderColor: 'border-amber-200 dark:border-amber-800',
          iconColor: 'text-amber-500',
          titleColor: 'text-amber-800 dark:text-amber-200'
        };
      case 'server':
        return {
          title: 'サーバーエラー',
          icon: Server,
          description: 'サーバーで問題が発生しました。しばらく待ってから再試行してください。',
          bgColor: 'bg-red-50 dark:bg-red-950/20',
          borderColor: 'border-red-200 dark:border-red-800',
          iconColor: 'text-red-500',
          titleColor: 'text-red-800 dark:text-red-200'
        };
      default:
        return {
          title: 'エラーが発生しました',
          icon: AlertCircle,
          description: '予期しないエラーが発生しました。',
          bgColor: 'bg-red-50 dark:bg-red-950/20',
          borderColor: 'border-red-200 dark:border-red-800',
          iconColor: 'text-red-500',
          titleColor: 'text-red-800 dark:text-red-200'
        };
    }
  };

  const config = getErrorConfig(errorState.type);
  const IconComponent = config.icon;

  if (variant === "compact") {
    return (
      <div className={cn(
        "flex items-center gap-3 p-3 rounded-lg border",
        config.bgColor,
        config.borderColor,
        className
      )}>
        <IconComponent className={cn("h-4 w-4 flex-shrink-0", config.iconColor)} />
        <div className="flex-1 min-w-0">
          <p className={cn("text-sm font-medium", config.titleColor)}>
            {config.title}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {errorState.message || config.description}
          </p>
        </div>
        <div className="flex items-center gap-1">
          {errorState.retryable && onRetry && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRetry}
              className="h-7 px-2 text-xs hover:bg-white/50 dark:hover:bg-black/20"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              再試行
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="h-7 w-7 p-0 hover:bg-white/50 dark:hover:bg-black/20"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div className={cn(
        "flex items-center gap-2 text-sm",
        config.titleColor,
        className
      )}>
        <IconComponent className={cn("h-4 w-4", config.iconColor)} />
        <span>{errorState.message || config.description}</span>
        {errorState.retryable && onRetry && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRetry}
            className="h-6 px-2 text-xs ml-2"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            再試行
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-2 mb-2 rounded-md border-l-4 text-sm relative",
        config.bgColor,
        config.borderColor,
        "border-l-current",
        className
      )}
    >
      <IconComponent className={cn("h-4 w-4 flex-shrink-0", config.iconColor)} />
      <div className="flex-1 min-w-0 pr-6">
        <span className={cn("font-medium", config.titleColor)}>
          {config.title}:
        </span>{" "}
        <span className="text-muted-foreground">
          {errorState.message || config.description}
        </span>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={cn(
            "absolute top-1 right-1 h-5 w-5 flex items-center justify-center rounded transition-colors",
            "hover:bg-black/10 dark:hover:bg-white/10"
          )}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}
