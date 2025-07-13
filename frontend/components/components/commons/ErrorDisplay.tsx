"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/components/ui/alert";
import { Button } from "@/components/components/ui/button";
import { AlertCircle, RefreshCw, X } from "lucide-react";
import { ErrorState } from "../../hooks/useErrorHandling";

interface ErrorDisplayProps {
  error: ErrorState | string;
  onDismiss?: () => void;
  onRetry?: () => void;
  className?: string;
}

/**
 * Common component for displaying errors with retry and dismiss functionality
 */
export function ErrorDisplay({ error, onDismiss, onRetry, className }: ErrorDisplayProps) {
  const errorState = typeof error === 'string'
    ? { message: error, type: 'unknown' as const, retryable: true }
    : error;

  const getErrorTitle = (type: ErrorState['type']): string => {
    switch (type) {
      case 'network':
        return 'ネットワークエラー';
      case 'validation':
        return '入力エラー';
      case 'server':
        return 'サーバーエラー';
      default:
        return 'エラーが発生しました';
    }
  };

  return (
    <Alert variant="destructive" className={`mb-4 ${className || ''}`}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="flex items-center justify-between">
        <span>{getErrorTitle(errorState.type)}</span>
        <div className="flex gap-2">
          {errorState.retryable && onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="h-6 px-2 text-xs"
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
              className="h-6 w-6 p-0"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </AlertTitle>
      <AlertDescription>
        {errorState.message}
      </AlertDescription>
    </Alert>
  );
}
