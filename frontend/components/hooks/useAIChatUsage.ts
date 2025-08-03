"use client";

import {
  AIChatUsage,
  AIChatUsageError,
  AI_CHAT_USAGE_ERROR_CODES,
  AI_CHAT_USAGE_ERROR_MESSAGES
} from "@/types/AIChatUsage";
import { useCallback, useEffect, useState } from "react";
import { useErrorHandling } from "./useErrorHandling";

interface UseAIChatUsageReturn {
  // State
  usage: AIChatUsage | null;
  loading: boolean;

  // Actions
  checkUsage: () => Promise<void>;
  refreshUsage: () => Promise<void>;
  incrementUsage: () => Promise<AIChatUsage | null>;

  // Error handling
  error: AIChatUsageError | null;
  clearError: () => void;

  // Real-time updates
  isUsageExhausted: boolean;
  canUseChat: boolean;
}

/**
 * Custom hook for managing AI Chat usage limits and tracking
 * Provides real-time usage information and error handling
 *
 * Requirements covered:
 * - 4.1: Real-time usage status display
 * - 4.2: Usage limit checking and form control
 * - 5.1: Error handling with user-friendly messages
 * - 5.2: API communication and state management
 */
export function useAIChatUsage(): UseAIChatUsageReturn {
  // State management
  const [usage, setUsage] = useState<AIChatUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [usageError, setUsageError] = useState<AIChatUsageError | null>(null);

  // General error handling for system errors
  const { error: systemError, withErrorHandling, clearError: clearSystemError } = useErrorHandling();

  // Clear all errors
  const clearError = useCallback(() => {
    setUsageError(null);
    clearSystemError();
  }, [clearSystemError]);

  // Fetch usage information from backend API
  const fetchUsageData = useCallback(async (): Promise<void> => {
    try {
      const response = await fetch('/api/ai/usage', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Handle HTTP error responses
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
      // System/network errors
      const errorMessage = err instanceof Error ? err.message : 'システムエラーが発生しました';

      setUsageError({
        error: AI_CHAT_USAGE_ERROR_MESSAGES[AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR],
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
        resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
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
          // Additional system error handling if needed
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
          // Usage limit or plan restriction errors
          const errorData: AIChatUsageError = await response.json();
          setUsageError(errorData);
          setUsage(null);
          return null;
        }

        // Other HTTP errors
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Success response - update local state
      const updatedUsage: AIChatUsage = await response.json();
      setUsage(updatedUsage);
      setUsageError(null);

      return updatedUsage;

    } catch (err) {
      // System/network errors
      const errorMessage = err instanceof Error ? err.message : 'システムエラーが発生しました';

      const systemError: AIChatUsageError = {
        error: AI_CHAT_USAGE_ERROR_MESSAGES[AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR],
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
        resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      setUsageError(systemError);
      setUsage(null);

      // Log system error for debugging
      if (process.env.NODE_ENV === 'development') {
        console.error('AI Chat Usage Increment Error:', errorMessage);
      }

      return null;
    }
  }, []);

  // Auto-refresh usage data periodically (every 5 minutes)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!loading) {
        fetchUsageData();
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [fetchUsageData, loading]);

  // Initial data fetch
  useEffect(() => {
    checkUsage();
  }, [checkUsage]);

  // Determine the primary error to return (usage errors take precedence)
  const primaryError = usageError || (systemError ? {
    error: AI_CHAT_USAGE_ERROR_MESSAGES[AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR],
    errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
    remainingCount: 0,
    resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  } : null);

  // Computed values for easier usage in components
  const isUsageExhausted = usage ? usage.remainingCount <= 0 : true;
  const canUseChat = usage ? usage.canUseChat : false;

  return {
    // State
    usage,
    loading,

    // Actions
    checkUsage,
    refreshUsage,
    incrementUsage,

    // Error handling
    error: primaryError,
    clearError,

    // Real-time updates
    isUsageExhausted,
    canUseChat,
  };
}