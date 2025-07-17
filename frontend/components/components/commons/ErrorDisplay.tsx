"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/components/ui/alert";
import { Button } from "@/components/components/ui/button";
import { AlertCircle, RefreshCw, X, WifiOff, AlertTriangle, Server } from "lucide-react";
import { ErrorState } from "../../hooks/useErrorHandling";
import { cn } from "@/components/lib/utils";

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
    <Alert
      className={cn(
        "mb-6 border-l-4 shadow-sm animate-fade-in-up",
        config.bgColor,
        config.borderColor,
        "border-l-current",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <IconComponent className={cn("h-5 w-5 mt-0.5 flex-shrink-0 animate-gentle-bounce", config.iconColor)} />
        <div className="flex-1 min-w-0">
          <AlertTitle className={cn(
            "text-base font-semibold mb-2 flex items-center justify-between",
            config.titleColor
          )}>
            <span>{config.title}</span>
            <div className="flex items-center gap-2">
              {errorState.retryable && onRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRetry}
                  className={cn(
                    "h-8 px-3 text-xs font-medium transition-all duration-300 ease-out",
                    "hover:scale-105 hover:shadow-sm active:scale-95",
                    "border-current/20 hover:border-current/40",
                    "bg-white/50 hover:bg-white/80 dark:bg-black/20 dark:hover:bg-black/40"
                  )}
                >
                  <RefreshCw className="h-3 w-3 mr-2 transition-transform duration-200" />
                  再試行
                </Button>
              )}
              {onDismiss && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDismiss}
                  className={cn(
                    "h-8 w-8 p-0 transition-all duration-300 ease-out",
                    "hover:scale-105 hover:bg-white/50 dark:hover:bg-black/20 active:scale-95"
                  )}
                >
                  <X className="h-4 w-4 transition-transform duration-200" />
                </Button>
              )}
            </div>
          </AlertTitle>
          <AlertDescription className="text-sm leading-relaxed text-muted-foreground">
            {errorState.message || config.description}
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}
