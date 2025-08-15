import { ErrorCode } from "@/constants/error_messages";
import { AIChatUsage, AIChatUsageError, PLAN_LIMITS, SubscriptionPlan } from "@/types/AIChatUsage";
import { apiGet } from "@/utils/api";
import { auth, clerkClient } from '@clerk/nextjs/server';
import { NextResponse } from "next/server";

/**
 * 暫定対応: すべての機能を統合したシンプルな実装
 * TODO: Clerk Python SDKが修正されたら削除予定
 *
 * Temporary workaround: All functionality integrated in simple implementation
 * This should be deleted once the Clerk Python SDK is fixed.
 */

// シンプルなログ機能
// Simple logging functionality
function workaroundLog(level: 'info' | 'warn' | 'error', message: string, data?: Record<string, unknown>): void {
  const timestamp = new Date().toISOString();
  const logMessage = `[WORKAROUND] ${timestamp} ${message}`;

  switch (level) {
    case 'info':
      console.info(logMessage, data || {});
      break;
    case 'warn':
      console.warn(logMessage, data || {});
      break;
    case 'error':
      console.error(logMessage, data || {});
      break;
  }
}

// 安全な実行（絶対に例外を投げない）
// Safe execution (never throws exceptions)
async function safeExecute<T>(
  operation: () => Promise<T>,
  fallbackValue: T,
  operationName: string
): Promise<T> {
  try {
    // タイムアウト付きで実行
    // Execute with timeout
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('Operation timeout')), 5000);
    });

    const result = await Promise.race([operation(), timeoutPromise]);
    workaroundLog('info', `${operationName} succeeded`);
    return result;

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    workaroundLog('error', `${operationName} failed, using fallback`, { error: errorMessage });
    return fallbackValue;
  }
}

// Clerkからプラン情報を取得
// Retrieve plan information from Clerk
async function getClerkPlan(): Promise<{
  plan: string;
  success: boolean;
  error?: string;
  source: 'subscription' | 'metadata' | 'fallback';
}> {
  try {
    const { userId } = await auth();

    if (!userId) {
      throw new Error('User not authenticated');
    }

    const client = await clerkClient();
    const user = await client.users.getUser(userId);

    workaroundLog('info', 'Retrieved user data from Clerk', {
      hasPublicMetadata: !!user.publicMetadata,
      hasPrivateMetadata: !!user.privateMetadata
    });

    // 1. サブスクリプション情報から取得を試行
    // Try to get plan from subscription information
    if (user.publicMetadata?.subscription) {
      const subscription = user.publicMetadata.subscription as Record<string, unknown>;
      if (subscription.plan) {
        const planName = String(subscription.plan).toLowerCase();
        if (planName === 'free' || planName === 'standard') {
          workaroundLog('info', 'Plan found in subscription metadata', { plan: planName });
          return {
            plan: planName,
            success: true,
            source: 'subscription'
          };
        }
      }
    }

    // 2. メタデータから直接取得を試行
    // Try to get plan directly from metadata
    if (user.publicMetadata?.plan) {
      const planName = String(user.publicMetadata.plan).toLowerCase();
      if (planName === 'free' || planName === 'standard') {
        return {
          plan: planName,
          success: true,
          source: 'metadata'
        };
      }
    }

    // 3. プライベートメタデータもチェック
    // Check private metadata as well
    if (user.privateMetadata?.plan) {
      const planName = String(user.privateMetadata.plan).toLowerCase();
      if (planName === 'free' || planName === 'standard') {
        return {
          plan: planName,
          success: true,
          source: 'metadata'
        };
      }
    }

    // 4. フォールバック - デフォルトでfreeプランを返す
    // Fallback - return free plan as default
    return {
      plan: 'free',
      success: true,
      source: 'fallback'
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    workaroundLog('error', 'Error retrieving plan from Clerk', { error: errorMessage });

    return {
      plan: 'free',
      success: false,
      error: errorMessage,
      source: 'fallback'
    };
  }
}

// プラン情報を上書き
// Override plan information
function overridePlanInformation(
  backendResponse: AIChatUsage,
  clerkPlan: { plan: string; success: boolean; error?: string; source: string }
): {
  data: AIChatUsage;
  wasOverridden: boolean;
  originalPlan?: string;
  newPlan?: string;
  error?: string;
} {
  try {
    workaroundLog('info', 'Starting plan override process', {
      originalPlan: backendResponse.plan_name,
      clerkPlan: clerkPlan.plan,
      clerkSuccess: clerkPlan.success
    });

    // フロントエンドでのプラン取得が失敗した場合は上書きしない
    // Don't override if frontend plan retrieval failed
    if (!clerkPlan.success) {
      workaroundLog('warn', 'Plan override skipped due to Clerk plan retrieval failure', {
        error: clerkPlan.error
      });

      return {
        data: backendResponse,
        wasOverridden: false,
        error: clerkPlan.error
      };
    }

    const originalPlan = backendResponse.plan_name;
    const newPlan = clerkPlan.plan as SubscriptionPlan;

    // プラン名の有効性を検証
    // Validate plan name
    if (newPlan !== 'free' && newPlan !== 'standard') {
      const errorMsg = `Invalid plan name: ${newPlan}`;
      workaroundLog('warn', 'Plan override failed due to invalid plan name', {
        originalPlan,
        invalidPlan: newPlan
      });

      return {
        data: backendResponse,
        wasOverridden: false,
        error: errorMsg
      };
    }

    // プランが同じ場合は上書き不要
    // No override needed if plans are the same
    if (originalPlan === newPlan) {
      workaroundLog('info', 'Plan override not needed - plans are identical', {
        plan: originalPlan
      });

      return {
        data: backendResponse,
        wasOverridden: false,
        originalPlan,
        newPlan
      };
    }

    // プラン情報を上書きして関連フィールドを再計算
    // Override plan info and recalculate related fields
    const newDailyLimit = PLAN_LIMITS[newPlan];
    const currentUsage = backendResponse.current_usage || 0;
    const newRemainingCount = Math.max(0, newDailyLimit - currentUsage);
    const newCanUseChat = newDailyLimit > 0 && currentUsage < newDailyLimit;

    // 計算結果の妥当性をチェック
    // Validate calculation results
    if (newDailyLimit < 0 || newRemainingCount < 0) {
      throw new Error(`Invalid calculation results: dailyLimit=${newDailyLimit}, remainingCount=${newRemainingCount}`);
    }

    const overriddenResponse: AIChatUsage = {
      ...backendResponse,
      plan_name: newPlan,
      daily_limit: newDailyLimit,
      remaining_count: newRemainingCount,
      can_use_chat: newCanUseChat
    };

    workaroundLog('info', 'Plan override completed successfully', {
      originalPlan,
      newPlan,
      originalLimit: backendResponse.daily_limit,
      newLimit: overriddenResponse.daily_limit,
      currentUsage: backendResponse.current_usage
    });

    return {
      data: overriddenResponse,
      wasOverridden: true,
      originalPlan,
      newPlan
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    workaroundLog('error', 'Unexpected error in plan override', {
      error: errorMessage,
      originalPlan: backendResponse.plan_name
    });

    return {
      data: backendResponse,
      wasOverridden: false,
      error: errorMessage
    };
  }
}

/**
 * GET /api/ai/usage
 * Fetch AI Chat usage information for the authenticated user
 *
 * 暫定対応: バックエンドのClerk Python SDK問題により、
 * フロントエンドでプラン情報を取得してレスポンスを上書き
 * Temporary workaround: Due to Clerk Python SDK issues in backend,
 * retrieve plan info on frontend and override response
 *
 * Returns:
 * - 200: AIChatUsage object with current usage stats
 * - 403: Plan restriction error (free plan users)
 * - 429: Usage limit exceeded error
 * - 500: System error
 */
export async function GET(): Promise<NextResponse> {
  try {
    // バックエンドAPIからの基本レスポンス取得
    // Get basic response from backend API
    const response = await apiGet<AIChatUsage>('/ai/usage');

    if (response.error) {
      // エラーレスポンスの処理（既存ロジック）
      // Handle error responses (existing logic)
      const status = response.error.status || 500;

      // For usage-related errors (403, 429), return the error details
      if (status === 403 || status === 429) {
        const errorResponse: AIChatUsageError = {
          error: response.error.message,
          error_code: response.error.details?.error_code || 'SYSTEM_ERROR',
          remaining_count: response.error.details?.remaining_count || 0,
          reset_time: response.error.details?.reset_time || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        };

        return NextResponse.json(errorResponse, { status });
      }

      // For other errors, return generic error response
      return NextResponse.json(
        {
          error: response.error.message || 'システムエラーが発生しました',
          error_code: 'SYSTEM_ERROR',
          remaining_count: 0,
          reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        } as AIChatUsageError,
        { status }
      );
    }

    // 暫定対応: プラン情報の上書き処理
    // Temporary workaround: Plan information override process
    if (response.data) {
      try {
        workaroundLog('info', 'Starting plan override process');

        // 安全なプラン取得
        // Safe plan retrieval
        const clerkPlan = await safeExecute(
          () => getClerkPlan(),
          {
            plan: 'free',
            success: false,
            error: 'Safe execution fallback',
            source: 'fallback'
          },
          'clerkPlanRetrieval'
        );

        workaroundLog('info', 'Clerk plan retrieved', {
          plan: clerkPlan.plan,
          success: clerkPlan.success,
          source: clerkPlan.source
        });

        // 安全なプラン上書き
        // Safe plan override
        const overrideResult = await safeExecute(
          () => Promise.resolve(overridePlanInformation(response.data!, clerkPlan)),
          {
            data: response.data!,
            wasOverridden: false,
            error: 'Safe override fallback'
          },
          'planOverride'
        );

        if (overrideResult.wasOverridden) {
          workaroundLog('info', 'Plan information overridden successfully', {
            originalPlan: overrideResult.originalPlan,
            newPlan: overrideResult.newPlan
          });
        }

        return NextResponse.json(overrideResult.data);

      } catch (workaroundError) {
        // 暫定対応でエラーが発生した場合は元のレスポンスを返す
        // Return original response if workaround fails
        const errorMessage = workaroundError instanceof Error ? workaroundError.message : String(workaroundError);
        workaroundLog('error', 'Workaround process failed, using original response', {
          error: errorMessage
        });

        return NextResponse.json(response.data);
      }
    }

    // Success response (fallback)
    return NextResponse.json(response.data);

  } catch (error) {
    // 既存のエラーハンドリング（シンプル版）
    // Simplified existing error handling
    const errorMessage = error instanceof Error ? error.message : String(error);

    // エラーの重要度を判定
    // Determine error severity
    let errorSeverity: 'low' | 'medium' | 'high' = 'medium';
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      if (message.includes('unauthorized') || message.includes('forbidden') || message.includes('authentication')) {
        errorSeverity = 'high';
      } else if (message.includes('network') || message.includes('timeout') || message.includes('connection')) {
        errorSeverity = 'medium';
      } else {
        errorSeverity = 'low';
      }
    }

    workaroundLog('error', 'AI Usage API Error', {
      error: errorMessage,
      severity: errorSeverity
    });

    // エラーの重要度に応じてレスポンスを調整
    // Adjust response based on error severity
    const status = errorSeverity === 'high' ? 503 : 500;
    const errorCode: ErrorCode = 'SYSTEM_ERROR';

    const errorResponse: AIChatUsageError = {
      error: 'システムエラーが発生しました',
      error_code: errorCode,
      remaining_count: 0,
      reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    };

    return NextResponse.json(errorResponse, { status });
  }
}