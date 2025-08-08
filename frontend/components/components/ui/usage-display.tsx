/**
 * UsageDisplay Component
 *
 * レスポンシブなAIチャット利用状況表示コンポーネント
 * モバイル・タブレット・デスクトップ対応のレスポンシブデザイン
 * 2プラン対応（free, standard）でTailwind CSSを使用したスタイリング
 */

import { Alert, AlertDescription } from '@/components/components/ui/alert';
import { Badge } from '@/components/components/ui/badge';
import { Card, CardContent } from '@/components/components/ui/card';
import { Skeleton } from '@/components/components/ui/skeleton';
import { cn } from '@/components/lib/utils';
import {
  AccessibilityMessages,
  ErrorMessages,
  getErrorAction,
  getErrorMessage,
  hasErrorAction,
  PlanMessages,
  UsageMessages
} from '@/constants/error_messages';
import { AIChatUsageError, SubscriptionPlan, UsageDisplayProps } from '@/types/AIChatUsage';
import { AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import React from 'react';

/**
 * UsageDisplayコンポーネント
 * 設計要件に従ったレスポンシブUI実装
 *
 * @example
 * ```tsx
 * // 詳細表示（デフォルト）
 * <UsageDisplay
 *   currentUsage={5}
 *   dailyLimit={10}
 *   planName="standard"
 *   variant="detailed"
 *   showResetTime={true}
 * />
 *
 * // コンパクト表示
 * <UsageDisplay
 *   currentUsage={2}
 *   dailyLimit={10}
 *   planName="standard"
 *   variant="compact"
 * />
 *
 * // ミニマル表示
 * <UsageDisplay
 *   currentUsage={0}
 *   dailyLimit={0}
 *   planName="free"
 *   variant="minimal"
 * />
 * ```
 */
export const UsageDisplay: React.FC<UsageDisplayProps> = ({
  currentUsage,
  dailyLimit,
  planName,
  className = '',
  variant = 'detailed',
  showResetTime = true,
  resetTime,
  loading = false,
  error = null,
}) => {
  // 残り利用回数を計算
  const remainingCount = Math.max(0, dailyLimit - currentUsage);
  const usagePercentage = dailyLimit > 0 ? (currentUsage / dailyLimit) * 100 : 0;
  const isLimitReached = remainingCount === 0;
  const isFreePlan = planName === 'free';

  // エラー状態の処理
  if (loading) {
    return <UsageDisplaySkeleton variant={variant} className={className} />;
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error}
        variant={variant}
        className={className}
        planName={planName}
      />
    );
  }

  // バリアント別のレンダリング
  switch (variant) {
    case 'minimal':
      return (
        <MinimalUsageDisplay
          currentUsage={currentUsage}
          dailyLimit={dailyLimit}
          remainingCount={remainingCount}
          className={className}
          isLimitReached={isLimitReached}
          isFreePlan={isFreePlan}
        />
      );

    case 'compact':
      return (
        <CompactUsageDisplay
          currentUsage={currentUsage}
          remainingCount={remainingCount}
          dailyLimit={dailyLimit}
          planName={planName}
          className={className}
          isLimitReached={isLimitReached}
          isFreePlan={isFreePlan}
        />
      );

    case 'detailed':
    default:
      return (
        <DetailedUsageDisplay
          currentUsage={currentUsage}
          remainingCount={remainingCount}
          dailyLimit={dailyLimit}
          planName={planName}
          className={className}
          isLimitReached={isLimitReached}
          isFreePlan={isFreePlan}
          usagePercentage={usagePercentage}
          showResetTime={showResetTime}
          resetTime={resetTime}
        />
      );
  }
};

// Safe accessor for plan messages with a typed fallback to avoid lint any
const getPlanMessage = (plan: SubscriptionPlan) => {
  const fallback: { title: string; description: string; upgradeMessage: string | null } = {
    title: 'プラン不明',
    description: '',
    upgradeMessage: null,
  };
  return (PlanMessages as Record<string, typeof fallback>)[plan] ?? fallback;
};

/**
 * 詳細表示バリアント（デフォルト）
 * モバイル・タブレット・デスクトップ対応のレスポンシブレイアウト
 */
const DetailedUsageDisplay: React.FC<{
  currentUsage: number;
  remainingCount: number;
  dailyLimit: number;
  planName: SubscriptionPlan;
  className: string;
  isLimitReached: boolean;
  isFreePlan: boolean;
  usagePercentage: number;
  showResetTime: boolean;
  resetTime?: string;
}> = ({
  currentUsage,
  remainingCount,
  dailyLimit,
  planName,
  className,
  isLimitReached,
  isFreePlan,
  usagePercentage,
  showResetTime,
  resetTime,
}) => {
  const planInfo = getPlanMessage(planName);

    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="p-4 sm:p-6">
          {/* プラン情報とバッジ */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-2">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-blue-500" />
              <span className="font-medium text-sm sm:text-base">
                {planInfo.title}
              </span>
            </div>
            <Badge
              variant={isFreePlan ? "secondary" : isLimitReached ? "destructive" : "default"}
              className="text-xs"
            >
              {isFreePlan ? "利用不可" : isLimitReached ? "上限達成" : "利用可能"}
            </Badge>
          </div>

          {/* 利用状況表示 */}
          {!isFreePlan && (
            <>
              {/* 利用回数の表示 */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {isLimitReached ? (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    ) : (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      {UsageMessages.remainingCount(remainingCount)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {currentUsage}/{dailyLimit}回使用
                  </span>
                </div>

                {/* プログレスバー */}
                <div className="w-full bg-gray-200 rounded-full h-2" data-testid="usage-progress">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${isLimitReached
                        ? 'bg-red-500'
                        : usagePercentage > 75
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                    style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                    role="progressbar"
                    aria-valuenow={currentUsage}
                    aria-valuemin={0}
                    aria-valuemax={dailyLimit}
                    aria-label={AccessibilityMessages.usageStatus(remainingCount, dailyLimit, planName)}
                  />
                </div>
              </div>

              {/* リセット時間表示 */}
              {showResetTime && (
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
                  <Clock className="h-3 w-3 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    {resetTime ? `${resetTime}にリセット` : UsageMessages.resetTime}
                  </span>
                </div>
              )}
            </>
          )}

          {/* フリープランのアップグレードメッセージ */}
          {isFreePlan && planInfo.upgradeMessage && (
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-700">
                {planInfo.upgradeMessage}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

/**
 * コンパクト表示バリアント
 * 狭いスペース用の簡潔な表示
 */
const CompactUsageDisplay: React.FC<{
  currentUsage: number;
  remainingCount: number;
  dailyLimit: number;
  planName: SubscriptionPlan;
  className: string;
  isLimitReached: boolean;
  isFreePlan: boolean;
}> = ({
  currentUsage,
  remainingCount,
  dailyLimit,
  planName,
  className,
  isLimitReached,
  isFreePlan,
}) => {
    return (
  <div className={cn("flex items-center gap-3 p-3 bg-gray-50 rounded-lg", className)}>
        <div className="flex items-center gap-2 flex-1">
          {isFreePlan ? (
            <AlertCircle className="h-4 w-4 text-gray-400" />
          ) : isLimitReached ? (
            <AlertCircle className="h-4 w-4 text-red-500" />
          ) : (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
          <span className="text-sm font-medium">
            {isFreePlan ? "利用不可" : UsageMessages.remainingCount(remainingCount)}
          </span>
        </div>

        {!isFreePlan && (
          <div className="text-xs text-gray-500">
            {currentUsage}/{dailyLimit}
          </div>
        )}

        <Badge
          variant={isFreePlan ? "secondary" : isLimitReached ? "destructive" : "default"}
          className="text-xs"
        >
          {getPlanMessage(planName).title}
        </Badge>
      </div>
    );
  };

/**
 * ミニマル表示バリアント
 * 最小限の情報のみ表示
 */
const MinimalUsageDisplay: React.FC<{
  currentUsage: number;
  dailyLimit: number;
  remainingCount: number;
  className: string;
  isLimitReached: boolean;
  isFreePlan: boolean;
}> = ({
  currentUsage,
  dailyLimit,
  remainingCount,
  className,
  isLimitReached,
  isFreePlan,
}) => {
    return (
      <div className={cn("flex items-center gap-2", className)} data-testid="mobile-usage-display">
        {isFreePlan ? (
          <span className="text-sm text-gray-500">利用不可</span>
        ) : (
          <>
            <span className={`text-sm font-medium ${isLimitReached ? 'text-red-600' : 'text-green-600'}`}>
              残り利用回数:
            </span>
            <span className={`text-sm ${isLimitReached ? 'text-red-600' : 'text-green-600'}`}>
              {`残り${Number.isFinite(remainingCount) ? remainingCount : 0}回`}
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {`${Math.max(0, currentUsage)}/${Number.isFinite(dailyLimit) ? dailyLimit : 0}`}
            </span>
          </>
        )}
      </div>
    );
  };

/**
 * エラー表示コンポーネント
 */
const ErrorDisplay: React.FC<{
  error: AIChatUsageError;
  variant: 'compact' | 'detailed' | 'minimal';
  className: string;
  planName: SubscriptionPlan;
}> = ({ error, variant, className }) => {
  const errorMessage = getErrorMessage(error.error_code, variant === 'detailed');
  const hasAction = hasErrorAction(error.error_code);
  const actionText = getErrorAction(error.error_code);

  if (variant === 'minimal') {
    return (
      <div className={cn("text-sm text-red-600", className)}>
  {error.error || ErrorMessages[error.error_code] || UsageMessages.noUsageData}
      </div>
    );
  }

  return (
    <Alert className={cn(className)} variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="text-sm">
        <div className="space-y-2">
          <p>{errorMessage}</p>
          {hasAction && actionText && (
            <p className="text-xs text-red-700">
              {actionText}が必要です
            </p>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

/**
 * ローディング用スケルトンコンポーネント
 */
const UsageDisplaySkeleton: React.FC<{
  variant: 'compact' | 'detailed' | 'minimal';
  className: string;
}> = ({ variant, className }) => {
  if (variant === 'minimal') {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Skeleton className="h-4 w-16" />
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <div className={cn("flex items-center gap-3 p-3 bg-gray-50 rounded-lg", className)}>
        <Skeleton className="h-4 w-4 rounded-full" />
        <Skeleton className="h-4 w-20 flex-1" />
        <Skeleton className="h-4 w-8" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    );
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardContent className="p-4 sm:p-6">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
          <Skeleton className="h-4 w-32" />
        </div>
      </CardContent>
    </Card>
  );
};

export default UsageDisplay;
