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
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: '現在のプランではご利用いただけません',
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: '一時的なエラーが発生しました',
} as const;