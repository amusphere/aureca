/**
 * TypeScript type definitions for AI Chat Usage Limits feature
 * Based on the backend Pydantic models for type safety
 */

/**
 * Response type for AI chat usage information
 * Corresponds to AIChatUsageResponse in backend
 */
export interface AIChatUsage {
  /** Number of remaining chat uses for today */
  remainingCount: number;
  /** Daily limit for the user's subscription plan */
  dailyLimit: number;
  /** ISO 8601 timestamp when the usage count resets (next day 00:00) */
  resetTime: string;
  /** Whether the user can currently use AI chat */
  canUseChat: boolean;
}

/**
 * Error response type for AI chat usage limit violations
 * Corresponds to AIChatUsageError in backend
 */
export interface AIChatUsageError {
  /** Human-readable error message in Japanese */
  error: string;
  /** Machine-readable error code for programmatic handling */
  errorCode: string;
  /** Current remaining count (typically 0 when limit exceeded) */
  remainingCount: number;
  /** ISO 8601 timestamp when the usage count resets */
  resetTime: string;
}

/**
 * API response wrapper for usage check endpoints
 */
export interface AIChatUsageApiResponse {
  data?: AIChatUsage;
  error?: AIChatUsageError;
}

/**
 * Error codes for AI chat usage limits
 * Used for programmatic error handling in the frontend
 */
export const AI_CHAT_USAGE_ERROR_CODES = {
  USAGE_LIMIT_EXCEEDED: 'USAGE_LIMIT_EXCEEDED',
  PLAN_RESTRICTION: 'PLAN_RESTRICTION',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
} as const;

export type AIChatUsageErrorCode = typeof AI_CHAT_USAGE_ERROR_CODES[keyof typeof AI_CHAT_USAGE_ERROR_CODES];

/**
 * User-friendly error messages in Japanese
 * Maps error codes to display messages
 */
export const AI_CHAT_USAGE_ERROR_MESSAGES: Record<AIChatUsageErrorCode, string> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: '本日の利用回数上限に達しました',
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: '現在のプランではAIChatをご利用いただけません',
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: '一時的なエラーが発生しました',
} as const;

/**
 * Detailed error messages with additional context
 * Used for more comprehensive error display
 */
export const AI_CHAT_USAGE_DETAILED_ERROR_MESSAGES: Record<AIChatUsageErrorCode, {
  title: string;
  description: string;
  actionText?: string;
}> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: {
    title: '利用回数上限に達しました',
    description: '本日のAIChat利用回数が上限に達しています。明日の00:00にリセットされます。',
    actionText: 'プランをアップグレード',
  },
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: {
    title: 'プランの制限',
    description: '現在のプランではAIChatをご利用いただけません。プランをアップグレードしてご利用ください。',
    actionText: 'プランをアップグレード',
  },
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: {
    title: 'システムエラー',
    description: '一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。',
    actionText: '再試行',
  },
} as const;

/**
 * Placeholder messages for input fields based on error state
 */
export const AI_CHAT_USAGE_PLACEHOLDER_MESSAGES: Record<AIChatUsageErrorCode, string> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: '本日の利用回数上限に達しました。明日の00:00にリセットされます。',
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: '現在のプランではAIChatをご利用いただけません。プランをアップグレードしてください。',
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: '一時的なエラーが発生しました。しばらく後にお試しください。',
} as const;

/**
 * Utility functions for AI Chat Usage error handling and display
 */
export class AIChatUsageUtils {
  /**
   * Format reset time for display in Japanese locale
   * @param resetTime ISO 8601 timestamp string
   * @returns Formatted time string in Japanese
   */
  static formatResetTime(resetTime: string): string {
    try {
      const date = new Date(resetTime);
      return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Tokyo',
      });
    } catch (error) {
      console.error('Error formatting reset time:', error);
      return '明日の00:00';
    }
  }

  /**
   * Get time until reset in human-readable format
   * @param resetTime ISO 8601 timestamp string
   * @returns Human-readable time until reset
   */
  static getTimeUntilReset(resetTime: string): string {
    try {
      const now = new Date();
      const reset = new Date(resetTime);
      const diffMs = reset.getTime() - now.getTime();

      if (diffMs <= 0) {
        return 'まもなくリセット';
      }

      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `約${hours}時間${minutes > 0 ? minutes + '分' : ''}後`;
      } else if (minutes > 0) {
        return `約${minutes}分後`;
      } else {
        return '1分以内';
      }
    } catch (error) {
      console.error('Error calculating time until reset:', error);
      return '明日の00:00';
    }
  }

  /**
   * Get appropriate error message based on error code and context
   * @param errorCode Error code
   * @param context Additional context (detailed, placeholder, etc.)
   * @returns Appropriate error message
   */
  static getErrorMessage(
    errorCode: AIChatUsageErrorCode,
    context: 'simple' | 'detailed' | 'placeholder' = 'simple'
  ): string {
    switch (context) {
      case 'detailed':
        return AI_CHAT_USAGE_DETAILED_ERROR_MESSAGES[errorCode]?.description ||
          AI_CHAT_USAGE_ERROR_MESSAGES[errorCode];
      case 'placeholder':
        return AI_CHAT_USAGE_PLACEHOLDER_MESSAGES[errorCode];
      default:
        return AI_CHAT_USAGE_ERROR_MESSAGES[errorCode];
    }
  }

  /**
   * Get error title for detailed display
   * @param errorCode Error code
   * @returns Error title
   */
  static getErrorTitle(errorCode: AIChatUsageErrorCode): string {
    return AI_CHAT_USAGE_DETAILED_ERROR_MESSAGES[errorCode]?.title || 'エラー';
  }

  /**
   * Get action text for error recovery
   * @param errorCode Error code
   * @returns Action text or null if no action available
   */
  static getErrorActionText(errorCode: AIChatUsageErrorCode): string | null {
    return AI_CHAT_USAGE_DETAILED_ERROR_MESSAGES[errorCode]?.actionText || null;
  }

  /**
   * Check if error is recoverable (user can take action)
   * @param errorCode Error code
   * @returns True if error is recoverable
   */
  static isRecoverableError(errorCode: AIChatUsageErrorCode): boolean {
    return errorCode !== AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR;
  }

  /**
   * Format usage display text
   * @param remainingCount Remaining usage count
   * @param dailyLimit Daily limit
   * @returns Formatted usage text
   */
  static formatUsageDisplay(remainingCount: number, dailyLimit: number): string {
    if (dailyLimit === -1) {
      return '無制限';
    }
    return `${remainingCount}/${dailyLimit}`;
  }

  /**
   * Get usage status color class
   * @param remainingCount Remaining usage count
   * @param dailyLimit Daily limit
   * @returns CSS color class
   */
  static getUsageStatusColor(remainingCount: number, dailyLimit: number): string {
    if (dailyLimit === -1) {
      return 'text-green-600';
    }

    const usageRatio = remainingCount / dailyLimit;
    if (usageRatio <= 0) {
      return 'text-red-600';
    } else if (usageRatio <= 0.2) {
      return 'text-orange-600';
    } else {
      return 'text-green-600';
    }
  }
}