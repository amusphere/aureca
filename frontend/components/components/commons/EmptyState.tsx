"use client";

import { cn } from "@/components/lib/utils";
import { Button } from "@/components/components/ui/button";
import {
  FileX,
  Search,
  Plus,
  Inbox,
  Calendar,
  CheckCircle,
  AlertCircle,
  Wifi,
  RefreshCw
} from "lucide-react";

interface EmptyStateProps {
  type?: "no-data" | "no-results" | "no-tasks" | "no-emails" | "no-calendar" | "completed" | "error" | "offline";
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

/**
 * Enhanced empty state component with modern styling and improved messaging
 */
export function EmptyState({
  type = "no-data",
  title,
  description,
  actionLabel,
  onAction,
  className,
  size = "md",
  showIcon = true
}: EmptyStateProps) {
  const getEmptyStateConfig = (type: EmptyStateProps['type']) => {
    switch (type) {
      case 'no-tasks':
        return {
          icon: CheckCircle,
          title: 'タスクがありません',
          description: 'まだタスクが作成されていません。新しいタスクを作成して始めましょう。',
          actionLabel: 'タスクを作成',
          iconColor: 'text-blue-500',
          bgColor: 'bg-blue-50 dark:bg-blue-950/20'
        };
      case 'no-emails':
        return {
          icon: Inbox,
          title: 'メールがありません',
          description: 'メールボックスは空です。新しいメールが届くまでお待ちください。',
          actionLabel: '更新',
          iconColor: 'text-green-500',
          bgColor: 'bg-green-50 dark:bg-green-950/20'
        };
      case 'no-calendar':
        return {
          icon: Calendar,
          title: 'イベントがありません',
          description: 'カレンダーにイベントがありません。新しいイベントを作成しましょう。',
          actionLabel: 'イベントを作成',
          iconColor: 'text-purple-500',
          bgColor: 'bg-purple-50 dark:bg-purple-950/20'
        };
      case 'no-results':
        return {
          icon: Search,
          title: '検索結果がありません',
          description: '検索条件に一致する項目が見つかりませんでした。別のキーワードで試してください。',
          actionLabel: '検索をクリア',
          iconColor: 'text-amber-500',
          bgColor: 'bg-amber-50 dark:bg-amber-950/20'
        };
      case 'completed':
        return {
          icon: CheckCircle,
          title: 'すべて完了しました！',
          description: 'おめでとうございます！すべてのタスクが完了しました。',
          actionLabel: '新しいタスクを作成',
          iconColor: 'text-green-500',
          bgColor: 'bg-green-50 dark:bg-green-950/20'
        };
      case 'error':
        return {
          icon: AlertCircle,
          title: 'データを読み込めませんでした',
          description: 'データの読み込み中にエラーが発生しました。再試行してください。',
          actionLabel: '再試行',
          iconColor: 'text-red-500',
          bgColor: 'bg-red-50 dark:bg-red-950/20'
        };
      case 'offline':
        return {
          icon: Wifi,
          title: 'オフラインです',
          description: 'インターネット接続を確認してください。接続が復旧すると自動的に更新されます。',
          actionLabel: '再接続を試行',
          iconColor: 'text-gray-500',
          bgColor: 'bg-gray-50 dark:bg-gray-950/20'
        };
      default:
        return {
          icon: FileX,
          title: 'データがありません',
          description: '表示するデータがありません。',
          actionLabel: '追加',
          iconColor: 'text-gray-500',
          bgColor: 'bg-gray-50 dark:bg-gray-950/20'
        };
    }
  };

  const config = getEmptyStateConfig(type);
  const IconComponent = config.icon;

  const sizeClasses = {
    sm: {
      container: "py-8 px-4",
      icon: "h-12 w-12",
      title: "text-lg",
      description: "text-sm",
      button: "h-8 px-3 text-xs"
    },
    md: {
      container: "py-12 px-6",
      icon: "h-16 w-16",
      title: "text-xl",
      description: "text-base",
      button: "h-10 px-4 text-sm"
    },
    lg: {
      container: "py-16 px-8",
      icon: "h-20 w-20",
      title: "text-2xl",
      description: "text-lg",
      button: "h-12 px-6 text-base"
    }
  };

  const currentSize = sizeClasses[size];

  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center animate-fade-in-up",
      currentSize.container,
      className
    )}>
      {showIcon && (
        <div className={cn(
          "rounded-full p-4 mb-4 transition-all duration-300 ease-out hover:scale-110 animate-gentle-bounce",
          config.bgColor
        )}>
          <IconComponent className={cn(
            currentSize.icon,
            config.iconColor,
            "transition-transform duration-300"
          )} />
        </div>
      )}

      <h3 className={cn(
        "font-semibold text-foreground mb-2 animate-fade-in-up",
        currentSize.title
      )} style={{ animationDelay: '0.1s' }}>
        {title || config.title}
      </h3>

      <p className={cn(
        "text-muted-foreground mb-6 max-w-md leading-relaxed animate-fade-in-up",
        currentSize.description
      )} style={{ animationDelay: '0.2s' }}>
        {description || config.description}
      </p>

      {(onAction || actionLabel) && (
        <Button
          onClick={onAction}
          className={cn(
            "transition-all duration-300 ease-out hover:scale-105 active:scale-95 hover:shadow-lg animate-fade-in-up",
            currentSize.button
          )}
          style={{ animationDelay: '0.3s' }}
        >
          {type === 'error' || type === 'offline' ? (
            <RefreshCw className="h-4 w-4 mr-2 transition-transform duration-200" />
          ) : (
            <Plus className="h-4 w-4 mr-2 transition-transform duration-200" />
          )}
          {actionLabel || config.actionLabel}
        </Button>
      )}
    </div>
  );
}