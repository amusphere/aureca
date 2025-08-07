/**
 * TypeScript type definitions for AI Chat Usage Limits feature
 * Based on the backend Pydantic models for type safety
 * Updated for 2-plan system (free and standard) with Clerk API integration
 */

/**
 * Supported subscription plans
 */
export type SubscriptionPlan = 'free' | 'standard';

/**
 * Plan limits constants matching backend PlanLimits
 */
export const PLAN_LIMITS: Record<SubscriptionPlan, number> = {
  free: 0,      // No AI chat access
  standard: 10, // 10 chats per day
} as const;

/**
 * Response type for AI chat usage information
 * Corresponds to AIChatUsageResponse in backend
 */
export interface AIChatUsage {
  /** Number of remaining chat uses for today */
  remaining_count: number;
  /** Daily limit for the user's subscription plan */
  daily_limit: number;
  /** ISO 8601 timestamp when the usage count resets (next day 00:00) */
  reset_time: string;
  /** Whether the user can currently use AI chat */
  can_use_chat: boolean;
  /** User's current subscription plan */
  plan_name?: SubscriptionPlan;
  /** Current usage count for today */
  current_usage?: number;
}

/**
 * Error response type for AI chat usage limit violations
 * Corresponds to AIChatUsageError in backend
 */
export interface AIChatUsageError {
  /** Human-readable error message in Japanese */
  error: string;
  /** Machine-readable error code for programmatic handling */
  error_code: string;
  /** Current remaining count (typically 0 when limit exceeded) */
  remaining_count: number;
  /** ISO 8601 timestamp when the usage count resets */
  reset_time: string;
}

/**
 * API response wrapper for usage check endpoints
 */
export interface AIChatUsageApiResponse {
  data?: AIChatUsage;
  error?: AIChatUsageError;
}

/**
 * Props for responsive usage display component
 * Supports mobile, tablet, and desktop layouts
 */
export interface UsageDisplayProps {
  /** Current usage count for today */
  currentUsage: number;
  /** Daily limit for the user's plan */
  dailyLimit: number;
  /** User's subscription plan name */
  planName: SubscriptionPlan;
  /** Additional CSS classes for styling */
  className?: string;
  /** Display variant for different contexts */
  variant?: 'compact' | 'detailed' | 'minimal';
  /** Show reset time information */
  showResetTime?: boolean;
  /** Reset time for usage counter */
  resetTime?: string;
  /** Loading state */
  loading?: boolean;
  /** Error state */
  error?: AIChatUsageError | null;
}

/**
 * Props for responsive AI chat modal component
 */
export interface AIChatModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Function to close the modal */
  onClose: () => void;
  /** Usage information */
  usage: AIChatUsage | null;
  /** Loading state */
  loading: boolean;
  /** Error state */
  error: AIChatUsageError | null;
  /** Function to refresh usage data */
  onRefresh: () => Promise<void>;
  /** Additional CSS classes */
  className?: string;
  /** Mobile-optimized layout */
  isMobile?: boolean;
}

/**
 * Responsive breakpoint configuration
 */
export interface ResponsiveBreakpoints {
  /** Mobile breakpoint (default: 640px) */
  mobile: number;
  /** Tablet breakpoint (default: 768px) */
  tablet: number;
  /** Desktop breakpoint (default: 1024px) */
  desktop: number;
}

/**
 * Touch interface configuration for mobile devices
 */
export interface TouchInterfaceConfig {
  /** Enable touch gestures */
  enableGestures: boolean;
  /** Minimum touch target size (default: 44px) */
  minTouchTarget: number;
  /** Touch feedback enabled */
  touchFeedback: boolean;
}

/**
 * Custom hook return type for AI chat usage
 * Updated for responsive UI and error handling
 */
export interface UseAIChatUsageReturn {
  /** Current usage data */
  usage: AIChatUsage | null;
  /** Loading state */
  loading: boolean;
  /** Error state with Clerk API error support */
  error: AIChatUsageError | null;
  /** Function to check current usage */
  checkUsage: () => Promise<void>;
  /** Function to refresh usage data */
  refreshUsage: () => Promise<void>;
  /** Function to increment usage (for optimistic updates) */
  incrementUsage: () => Promise<void>;
  /** Whether user can use chat based on current state */
  canUseChat: boolean;
  /** Formatted usage display text */
  usageDisplayText: string;
  /** Time until reset in human-readable format */
  timeUntilReset: string;
}

/**
 * Error codes for AI chat usage limits
 * Used for programmatic error handling in the frontend
 * Updated to include Clerk API errors
 */
export const AI_CHAT_USAGE_ERROR_CODES = {
  USAGE_LIMIT_EXCEEDED: 'USAGE_LIMIT_EXCEEDED',
  PLAN_RESTRICTION: 'PLAN_RESTRICTION',
  CLERK_API_ERROR: 'CLERK_API_ERROR',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
} as const;

export type AIChatUsageErrorCode = typeof AI_CHAT_USAGE_ERROR_CODES[keyof typeof AI_CHAT_USAGE_ERROR_CODES];

/**
 * Device type for responsive design
 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop';

/**
 * Display variant for usage components
 */
export type UsageDisplayVariant = 'compact' | 'detailed' | 'minimal';

/**
 * Theme configuration for usage display
 */
export interface UsageDisplayTheme {
  /** Primary color for normal state */
  primaryColor: string;
  /** Warning color for low usage */
  warningColor: string;
  /** Error color for no usage */
  errorColor: string;
  /** Background color */
  backgroundColor: string;
  /** Text color */
  textColor: string;
  /** Border radius */
  borderRadius: string;
}

/**
 * Animation configuration for responsive components
 */
export interface AnimationConfig {
  /** Enable animations */
  enabled: boolean;
  /** Animation duration in milliseconds */
  duration: number;
  /** Animation easing function */
  easing: string;
  /** Reduce motion for accessibility */
  respectReducedMotion: boolean;
}

/**
 * Accessibility configuration for usage components
 */
export interface AccessibilityConfig {
  /** Enable screen reader announcements */
  announceChanges: boolean;
  /** ARIA label for usage display */
  usageLabel: string;
  /** ARIA label for error states */
  errorLabel: string;
  /** High contrast mode support */
  highContrast: boolean;
}

/**
 * Complete configuration for usage display components
 */
export interface UsageDisplayConfig {
  /** Theme configuration */
  theme: UsageDisplayTheme;
  /** Animation settings */
  animation: AnimationConfig;
  /** Accessibility settings */
  accessibility: AccessibilityConfig;
  /** Responsive breakpoints */
  breakpoints: ResponsiveBreakpoints;
  /** Touch interface settings */
  touch: TouchInterfaceConfig;
}

/**
 * Default configuration values
 */
export const DEFAULT_USAGE_DISPLAY_CONFIG: UsageDisplayConfig = {
  theme: {
    primaryColor: 'text-green-600',
    warningColor: 'text-orange-600',
    errorColor: 'text-red-600',
    backgroundColor: 'bg-gray-50',
    textColor: 'text-gray-600',
    borderRadius: 'rounded-lg',
  },
  animation: {
    enabled: true,
    duration: 200,
    easing: 'ease-in-out',
    respectReducedMotion: true,
  },
  accessibility: {
    announceChanges: true,
    usageLabel: 'AI チャット利用状況',
    errorLabel: 'エラー状態',
    highContrast: false,
  },
  breakpoints: {
    mobile: 640,
    tablet: 768,
    desktop: 1024,
  },
  touch: {
    enableGestures: true,
    minTouchTarget: 44,
    touchFeedback: true,
  },
} as const;

/**
 * User-friendly error messages in Japanese
 * Maps error codes to display messages
 * Updated for 2-plan system and Clerk API errors
 */
export const AI_CHAT_USAGE_ERROR_MESSAGES: Record<AIChatUsageErrorCode, string> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: '本日の利用回数上限（10回）に達しました',
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: 'freeプランではAIChatをご利用いただけません',
  [AI_CHAT_USAGE_ERROR_CODES.CLERK_API_ERROR]: 'プラン情報の取得に失敗しました',
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: '一時的なエラーが発生しました',
} as const;

/**
 * Detailed error messages with additional context
 * Used for more comprehensive error display
 * Updated for 2-plan system and Clerk API errors
 */
export const AI_CHAT_USAGE_DETAILED_ERROR_MESSAGES: Record<AIChatUsageErrorCode, {
  title: string;
  description: string;
  actionText?: string;
}> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: {
    title: '利用回数上限に達しました',
    description: '本日のAIChat利用回数が上限（10回）に達しています。明日の00:00にリセットされます。',
    actionText: 'プランをアップグレード',
  },
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: {
    title: 'プランの制限',
    description: 'freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてご利用ください。',
    actionText: 'standardプランにアップグレード',
  },
  [AI_CHAT_USAGE_ERROR_CODES.CLERK_API_ERROR]: {
    title: 'プラン情報取得エラー',
    description: 'プラン情報の取得に失敗しました。しばらく後にお試しください。',
    actionText: '再試行',
  },
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: {
    title: 'システムエラー',
    description: '一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。',
    actionText: '再試行',
  },
} as const;

/**
 * Placeholder messages for input fields based on error state
 * Updated for 2-plan system and Clerk API errors
 */
export const AI_CHAT_USAGE_PLACEHOLDER_MESSAGES: Record<AIChatUsageErrorCode, string> = {
  [AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED]: '本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。',
  [AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION]: 'freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。',
  [AI_CHAT_USAGE_ERROR_CODES.CLERK_API_ERROR]: 'プラン情報の取得に失敗しました。しばらく後にお試しください。',
  [AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR]: '一時的なエラーが発生しました。しばらく後にお試しください。',
} as const;

/**
 * Utility functions for AI Chat Usage error handling and display
 */
export class AIChatUsageUtils {
  /**
   * Format reset time for display in Japanese locale
   * @param reset_time ISO 8601 timestamp string
   * @returns Formatted time string in Japanese
   */
  static formatResetTime(reset_time: string): string {
    try {
      const date = new Date(reset_time);
      if (isNaN(date.getTime())) {
        return '明日の00:00';
      }
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
   * @param reset_time ISO 8601 timestamp string
   * @returns Human-readable time until reset
   */
  static getTimeUntilReset(reset_time: string): string {
    try {
      const now = new Date();
      const reset = new Date(reset_time);

      if (isNaN(reset.getTime())) {
        return '明日の00:00';
      }

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
   * Format usage display text for 2-plan system
   * @param remaining_count Remaining usage count
   * @param daily_limit Daily limit
   * @param plan_name User's subscription plan
   * @returns Formatted usage text
   */
  static formatUsageDisplay(remaining_count: number, daily_limit: number, plan_name?: SubscriptionPlan): string {
    if (plan_name === 'free' || daily_limit === 0) {
      return '利用不可';
    }
    return `${remaining_count}/${daily_limit}`;
  }

  /**
   * Get plan display name in Japanese
   * @param plan_name Subscription plan
   * @returns Japanese plan name
   */
  static getPlanDisplayName(plan_name: SubscriptionPlan): string {
    const planNames: Record<SubscriptionPlan, string> = {
      free: 'フリープラン',
      standard: 'スタンダードプラン',
    };
    return planNames[plan_name];
  }

  /**
   * Check if plan allows AI chat usage
   * @param plan_name Subscription plan
   * @returns True if plan allows AI chat
   */
  static isPlanAllowsChat(plan_name: SubscriptionPlan): boolean {
    return PLAN_LIMITS[plan_name] > 0;
  }

  /**
   * Get daily limit for plan
   * @param plan_name Subscription plan
   * @returns Daily limit for the plan
   */
  static getPlanLimit(plan_name: SubscriptionPlan): number {
    return PLAN_LIMITS[plan_name];
  }

  /**
   * Get usage status color class for 2-plan system
   * @param remaining_count Remaining usage count
   * @param daily_limit Daily limit
   * @param plan_name User's subscription plan
   * @returns CSS color class
   */
  static getUsageStatusColor(remaining_count: number, daily_limit: number, plan_name?: SubscriptionPlan): string {
    if (plan_name === 'free' || daily_limit === 0) {
      return 'text-gray-500';
    }

    const usageRatio = remaining_count / daily_limit;
    if (usageRatio <= 0) {
      return 'text-red-600';
    } else if (usageRatio <= 0.2) {
      return 'text-orange-600';
    } else {
      return 'text-green-600';
    }
  }

  /**
   * Get responsive CSS classes based on screen size
   * @param baseClasses Base CSS classes
   * @param mobileClasses Mobile-specific classes
   * @param tabletClasses Tablet-specific classes
   * @param desktopClasses Desktop-specific classes
   * @returns Combined responsive CSS classes
   */
  static getResponsiveClasses(
    baseClasses: string,
    mobileClasses?: string,
    tabletClasses?: string,
    desktopClasses?: string
  ): string {
    const classes = [baseClasses];

    if (mobileClasses) {
      classes.push(mobileClasses);
    }

    if (tabletClasses) {
      classes.push(`sm:${tabletClasses}`);
    }

    if (desktopClasses) {
      classes.push(`lg:${desktopClasses}`);
    }

    return classes.join(' ');
  }

  /**
   * Check if current device is mobile based on screen width
   * @param width Screen width in pixels
   * @returns True if mobile device
   */
  static isMobileDevice(width: number): boolean {
    return width < 640; // Tailwind's sm breakpoint
  }

  /**
   * Check if current device is tablet based on screen width
   * @param width Screen width in pixels
   * @returns True if tablet device
   */
  static isTabletDevice(width: number): boolean {
    return width >= 640 && width < 1024; // Between sm and lg breakpoints
  }

  /**
   * Get appropriate touch target size for mobile devices
   * @param isMobile Whether the device is mobile
   * @returns Touch target size in pixels
   */
  static getTouchTargetSize(isMobile: boolean): number {
    return isMobile ? 44 : 32; // 44px for mobile (Apple HIG), 32px for desktop
  }

  /**
   * Validate subscription plan
   * @param plan_name Plan name to validate
   * @returns True if valid plan
   */
  static isValidPlan(plan_name: string): plan_name is SubscriptionPlan {
    return plan_name === 'free' || plan_name === 'standard';
  }

  /**
   * Check if error is related to Clerk API
   * @param errorCode Error code to check
   * @returns True if Clerk API error
   */
  static isClerkApiError(errorCode: AIChatUsageErrorCode): boolean {
    return errorCode === AI_CHAT_USAGE_ERROR_CODES.CLERK_API_ERROR;
  }

  /**
   * Get upgrade message for plan restrictions
   * @param currentPlan Current user plan
   * @returns Upgrade message
   */
  static getUpgradeMessage(currentPlan: SubscriptionPlan): string {
    if (currentPlan === 'free') {
      return 'standardプランにアップグレードしてAIChatをご利用ください。';
    }
    return 'プランをアップグレードしてより多くのAIChatをご利用ください。';
  }

  /**
   * Calculate usage percentage
   * @param remaining_count Remaining usage count
   * @param daily_limit Daily limit
   * @returns Usage percentage (0-100)
   */
  static getUsagePercentage(remaining_count: number, daily_limit: number): number {
    if (daily_limit === 0) return 0;
    const used = daily_limit - remaining_count;
    return Math.round((used / daily_limit) * 100);
  }

  /**
   * Get progress bar color based on usage
   * @param percentage Usage percentage
   * @returns CSS color class for progress bar
   */
  static getProgressBarColor(percentage: number): string {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-orange-500';
    return 'bg-green-500';
  }

  /**
   * Format time remaining until reset for accessibility
   * @param reset_time ISO 8601 timestamp string
   * @returns Screen reader friendly time description
   */
  static formatTimeForScreenReader(reset_time: string): string {
    try {
      const now = new Date();
      const reset = new Date(reset_time);

      if (isNaN(reset.getTime())) {
        return '明日の午前0時にリセットされます';
      }

      const diffMs = reset.getTime() - now.getTime();

      if (diffMs <= 0) {
        return 'まもなくリセットされます';
      }

      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `約${hours}時間${minutes > 0 ? minutes + '分' : ''}後にリセットされます`;
      } else if (minutes > 0) {
        return `約${minutes}分後にリセットされます`;
      } else {
        return '1分以内にリセットされます';
      }
    } catch (error) {
      console.error('Error formatting time for screen reader:', error);
      return '明日の午前0時にリセットされます';
    }
  }

  /**
   * Get ARIA live region politeness level based on error severity
   * @param errorCode Error code
   * @returns ARIA live politeness level
   */
  static getAriaLivePoliteness(errorCode: AIChatUsageErrorCode): 'polite' | 'assertive' {
    // System errors and Clerk API errors are more urgent
    if (errorCode === AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR ||
        errorCode === AI_CHAT_USAGE_ERROR_CODES.CLERK_API_ERROR) {
      return 'assertive';
    }
    return 'polite';
  }
}