/**
 * Error message constants for AI Chat Usage Limits feature
 * Provides user-friendly Japanese messages for various error scenarios
 * Supports 2-plan system (free and standard) with Clerk API integration
 */

/**
 * Error codes used throughout the application
 * Must match the backend error codes for consistency
 */
export const ErrorCodes = {
  USAGE_LIMIT_EXCEEDED: 'USAGE_LIMIT_EXCEEDED',
  PLAN_RESTRICTION: 'PLAN_RESTRICTION',
  CLERK_API_ERROR: 'CLERK_API_ERROR',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

/**
 * User-friendly error messages in Japanese
 * Provides clear, actionable feedback to users
 */
export const ErrorMessages: Record<ErrorCode, string> = {
  [ErrorCodes.USAGE_LIMIT_EXCEEDED]: '本日の利用回数上限（10回）に達しました',
  [ErrorCodes.PLAN_RESTRICTION]: 'freeプランではAIChatをご利用いただけません',
  [ErrorCodes.CLERK_API_ERROR]: 'プラン情報の取得に失敗しました',
  [ErrorCodes.SYSTEM_ERROR]: '一時的なエラーが発生しました',
} as const;

/**
 * Detailed error messages with additional context
 * Used for more comprehensive error descriptions
 */
export const DetailedErrorMessages: Record<ErrorCode, string> = {
  [ErrorCodes.USAGE_LIMIT_EXCEEDED]:
    '本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。',
  [ErrorCodes.PLAN_RESTRICTION]:
    'freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。',
  [ErrorCodes.CLERK_API_ERROR]:
    'プラン情報の取得に失敗しました。しばらく後にお試しください。',
  [ErrorCodes.SYSTEM_ERROR]:
    '一時的なエラーが発生しました。しばらく後にお試しください。',
} as const;

/**
 * Action button text for different error scenarios
 * Provides contextual call-to-action buttons
 */
export const ErrorActionButtons: Record<ErrorCode, string | null> = {
  [ErrorCodes.USAGE_LIMIT_EXCEEDED]: null, // No action available, must wait for reset
  [ErrorCodes.PLAN_RESTRICTION]: 'プランをアップグレード',
  [ErrorCodes.CLERK_API_ERROR]: '再試行',
  [ErrorCodes.SYSTEM_ERROR]: '再試行',
} as const;

/**
 * Plan-specific messages for usage status
 * Provides context about current plan limitations
 */
export const PlanMessages = {
  free: {
    title: 'Freeプラン',
    description: 'AIChatはご利用いただけません',
    upgradeMessage: 'standardプランにアップグレードすると、1日10回までAIChatをご利用いただけます。',
  },
  standard: {
    title: 'Standardプラン',
    description: '1日10回までAIChatをご利用いただけます',
    upgradeMessage: null, // No upgrade needed for standard plan
  },
} as const;

/**
 * General UI messages for usage display
 * Used in responsive components for consistent messaging
 */
export const UsageMessages = {
  remainingCount: (count: number) => `残り${count}回`,
  dailyLimit: (limit: number) => `1日${limit}回まで`,
  resetTime: '明日の00:00にリセット',
  loading: '読み込み中...',
  noUsageData: '利用状況を取得できませんでした',
  planUnknown: 'プラン情報が不明です',
} as const;

/**
 * Accessibility messages for screen readers
 * Ensures the application is accessible to all users
 */
export const AccessibilityMessages = {
  usageStatus: (remaining: number, limit: number, plan: string) =>
    `${plan}プラン: ${limit}回中${limit - remaining}回使用済み、残り${remaining}回`,
  errorAlert: (message: string) => `エラー: ${message}`,
  loadingStatus: 'AI Chat使用状況を読み込み中',
  refreshButton: '使用状況を更新',
  closeModal: 'モーダルを閉じる',
} as const;

/**
 * Helper function to get appropriate error message based on context
 * @param errorCode The error code to get message for
 * @param detailed Whether to return detailed message or brief one
 * @returns Appropriate error message
 */
export const getErrorMessage = (
  errorCode: ErrorCode,
  detailed: boolean = false
): string => {
  return detailed
    ? DetailedErrorMessages[errorCode]
    : ErrorMessages[errorCode];
};

/**
 * Helper function to check if an error has an associated action
 * @param errorCode The error code to check
 * @returns Whether the error has an associated action button
 */
export const hasErrorAction = (errorCode: ErrorCode): boolean => {
  return ErrorActionButtons[errorCode] !== null;
};

/**
 * Helper function to get error action button text
 * @param errorCode The error code to get action for
 * @returns Action button text or null if no action available
 */
export const getErrorAction = (errorCode: ErrorCode): string | null => {
  return ErrorActionButtons[errorCode];
};
