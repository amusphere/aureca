/**
 * useAIChatUsage Hook - Refactored for AI Chat Usage Limits System
 *
 * リファクタリングされたAIチャット利用制限管理フック
 * 新しいAPIインターフェース、Clerk APIエラーハンドリング、レスポンシブUI用の状態管理に対応
 *
 * Features:
 * - 新しいAPI インターフェースに対応
 * - Clerk API エラーハンドリング
 * - レスポンシブUI用の状態管理
 * - パフォーマンス最適化
 * - 2プラン（free, standard）対応
 */

"use client";

import {
  ErrorCodes,
  getErrorMessage,
  UsageMessages
} from "@/constants/error_messages";
import {
  AIChatUsage,
  AIChatUsageError,
  SubscriptionPlan
} from "@/types/AIChatUsage";
import { useCallback, useEffect, useRef, useState } from "react";
import { useErrorHandling } from "./useErrorHandling";

/**
 * Return interface for useAIChatUsage hook
 * 設計要件に従ったインターフェース定義
 */
interface UseAIChatUsageReturn {
  // Core usage data
  usage: AIChatUsage | null;
  loading: boolean;
  error: AIChatUsageError | null;

  // Usage statistics (computed values)
  remainingCount: number;
  dailyLimit: number;
  currentUsage: number;
  planName: SubscriptionPlan;
  canUseChat: boolean;
  isUsageExhausted: boolean;
  usagePercentage: number;

  // Actions
  checkUsage: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  incrementUsage: () => Promise<AIChatUsage | null>;
  clearError: () => void;

  // Responsive UI helpers
  isLimitApproaching: boolean; // 75%以上使用
  getStatusMessage: () => string;
  getStatusColor: () => 'green' | 'yellow' | 'red' | 'gray';

  // Real-time update controls
  pauseAutoRefresh: () => void;
  resumeAutoRefresh: () => void;
  isAutoRefreshPaused: boolean;
}

/**
 * Custom hook for managing AI Chat usage limits and tracking
 * Provides real-time usage information and error handling
 *
 * Requirements covered:
 * - 5.1: レスポンシブUIでの利用状況表示
 * - 5.2: Clerk API エラーハンドリング
 * - 4.1: 利用可不可チェック機能
 * - 4.2: パフォーマンス最適化
 */
export function useAIChatUsage(): UseAIChatUsageReturn {
  // Core state management
  const [usage, setUsage] = useState<AIChatUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [usageError, setUsageError] = useState<AIChatUsageError | null>(null);
  const [isAutoRefreshPaused, setIsAutoRefreshPaused] = useState(false);

  // Auto-refresh control
  const autoRefreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // General error handling for system errors
  const { error: systemError, withErrorHandling, clearError: clearSystemError } = useErrorHandling();

  // Clear all errors
  const clearError = useCallback(() => {
    setUsageError(null);
    clearSystemError();
  }, [clearSystemError]);

  // Fetch usage information from backend API with new interface
  const fetchUsageData = useCallback(async (): Promise<void> => {
    try {
      const response = await fetch('/api/ai/usage', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Handle HTTP error responses with new error handling
        if (response.status === 403 || response.status === 429) {
          // Usage limit or plan restriction errors
          const errorData: AIChatUsageError = await response.json();
          setUsageError(errorData);
          setUsage(null);
          return;
        }

        // Other HTTP errors
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Success response
      const data: AIChatUsage = await response.json();
      setUsage(data);
      setUsageError(null);

    } catch (err) {
      // System/network errors with new error constants
      const errorMessage = err instanceof Error ? err.message : 'システムエラーが発生しました';

      setUsageError({
        error: getErrorMessage(ErrorCodes.SYSTEM_ERROR, true),
        error_code: ErrorCodes.SYSTEM_ERROR,
        remaining_count: 0,
        reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      });

      setUsage(null);

      // Log system error for debugging
      if (process.env.NODE_ENV === 'development') {
        console.error('AI Chat Usage API Error:', errorMessage);
      }
    }
  }, []);

  // Check usage with error handling wrapper
  const checkUsage = useCallback(async (): Promise<void> => {
    setLoading(true);
    clearError();

    await withErrorHandling(
      async () => {
        await fetchUsageData();
      },
      {
        onError: (error) => {
          console.error('Usage check failed:', error);
        }
      }
    );

    setLoading(false);
  }, [withErrorHandling, fetchUsageData, clearError]);

  // Refresh usage data (alias for checkUsage for clarity)
  const refreshUsage = useCallback(async (): Promise<void> => {
    await checkUsage();
  }, [checkUsage]);

  // Increment usage count after successful AI chat usage
  const incrementUsage = useCallback(async (): Promise<AIChatUsage | null> => {
    try {
      const response = await fetch('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Handle HTTP error responses
        if (response.status === 403 || response.status === 429) {
          const errorData: AIChatUsageError = await response.json();
          setUsageError(errorData);
          setUsage(null);
          return null;
        }

        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Success response - update local state
      const updatedUsage: AIChatUsage = await response.json();
      setUsage(updatedUsage);
      setUsageError(null);

      return updatedUsage;

    } catch (err) {
      // System/network errors with new error handling
      const errorMessage = err instanceof Error ? err.message : 'システムエラーが発生しました';

      const systemError: AIChatUsageError = {
        error: getErrorMessage(ErrorCodes.SYSTEM_ERROR, true),
        error_code: ErrorCodes.SYSTEM_ERROR,
        remaining_count: 0,
        reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      setUsageError(systemError);
      setUsage(null);

      if (process.env.NODE_ENV === 'development') {
        console.error('AI Chat Usage Increment Error:', errorMessage);
      }

      return null;
    }
  }, []);

  // Auto-refresh controls for performance optimization
  const pauseAutoRefresh = useCallback(() => {
    setIsAutoRefreshPaused(true);
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current);
      autoRefreshIntervalRef.current = null;
    }
  }, []);

  const resumeAutoRefresh = useCallback(() => {
    setIsAutoRefreshPaused(false);
  }, []);

  // Auto-refresh usage data periodically (optimized)
  useEffect(() => {
    if (!isAutoRefreshPaused && !loading) {
      autoRefreshIntervalRef.current = setInterval(() => {
        fetchUsageData();
      }, 5 * 60 * 1000); // 5 minutes
    }

    return () => {
      if (autoRefreshIntervalRef.current) {
        clearInterval(autoRefreshIntervalRef.current);
      }
    };
  }, [fetchUsageData, loading, isAutoRefreshPaused]);

  // Initial data fetch
  useEffect(() => {
    checkUsage();
  }, [checkUsage]);

  // Computed values for easier usage in components
  const remainingCount = usage?.remaining_count ?? 0;
  const dailyLimit = usage?.daily_limit ?? 0;
  const currentUsage = usage?.current_usage ?? 0;
  const planName: SubscriptionPlan = usage?.plan_name ?? 'free';
  const canUseChat = usage?.can_use_chat ?? false;
  const isUsageExhausted = remainingCount <= 0;
  const usagePercentage = dailyLimit > 0 ? (currentUsage / dailyLimit) * 100 : 0;
  const isLimitApproaching = usagePercentage >= 75;

  // Responsive UI helper functions
  const getStatusMessage = useCallback((): string => {
    if (usageError) {
      return getErrorMessage(usageError.error_code, false);
    }

    if (planName === 'free') {
      return UsageMessages.noUsageData;
    }

    if (isUsageExhausted) {
      return UsageMessages.remainingCount(0);
    }

    return UsageMessages.remainingCount(remainingCount);
  }, [usageError, planName, isUsageExhausted, remainingCount]);

  const getStatusColor = useCallback((): 'green' | 'yellow' | 'red' | 'gray' => {
    if (usageError) return 'red';
    if (planName === 'free') return 'gray';
    if (isUsageExhausted) return 'red';
    if (isLimitApproaching) return 'yellow';
    return 'green';
  }, [usageError, planName, isUsageExhausted, isLimitApproaching]);

  // Determine the primary error to return (usage errors take precedence)
  const primaryError = usageError || (systemError ? {
    error: getErrorMessage(ErrorCodes.SYSTEM_ERROR, true),
    error_code: ErrorCodes.SYSTEM_ERROR,
    remaining_count: 0,
    reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  } : null);

  return {
    // Core usage data
    usage,
    loading,
    error: primaryError,

    // Usage statistics (computed values)
    remainingCount,
    dailyLimit,
    currentUsage,
    planName,
    canUseChat,
    isUsageExhausted,
    usagePercentage,

    // Actions
    checkUsage,
    refreshUsage,
    incrementUsage,
    clearError,

    // Responsive UI helpers
    isLimitApproaching,
    getStatusMessage,
    getStatusColor,

    // Real-time update controls
    pauseAutoRefresh,
    resumeAutoRefresh,
    isAutoRefreshPaused,
  };
}