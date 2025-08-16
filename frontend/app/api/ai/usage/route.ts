import { ErrorCode } from "@/constants/error_messages";
import { AIChatUsage, AIChatUsageError, PLAN_LIMITS, SubscriptionPlan } from "@/types/AIChatUsage";
import { apiGet } from "@/utils/api";
import { auth, clerkClient } from '@clerk/nextjs/server';
import { NextResponse } from "next/server";

/**
 * 🚨 暫定対応 - 削除予定 🚨
 * TEMPORARY WORKAROUND - SCHEDULED FOR DELETION
 *
 * 作成日: 2025-01-16
 * 削除予定: Clerk Python SDK修正後 (TBD)
 *
 * 【削除条件】
 * - Clerk Python SDKでサブスクリプションプラン情報が正常に取得できるようになったら削除
 * - バックエンドの /api/ai/usage エンドポイントが正しいプラン情報を返すようになったら削除
 *
 * 【削除対象】
 * - workaroundLog関数
 * - safeExecute関数
 * - getClerkPlan関数
 * - overridePlanInformation関数
 * - GET関数内の暫定対応処理ロジック
 *
 * 【削除手順】
 * 1. WORKAROUND_ENABLED = false に設定して1週間動作確認
 * 2. 問題なければ暫定対応コードを完全削除
 * 3. GET関数を簡素化されたバージョンに置き換え
 *
 * 詳細: .kiro/specs/frontend-clerk-plan-workaround/DELETION_GUIDE.md 参照
 */

// 🚨 削除予定: シンプルなログ機能 🚨
// TODO: Clerk Python SDK修正後に削除
// Simple logging functionality - TO BE DELETED
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

// 🚨 削除予定: 安全な実行（絶対に例外を投げない）🚨
// TODO: Clerk Python SDK修正後に削除
// Safe execution (never throws exceptions) - TO BE DELETED
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

// 🚨 削除予定: Clerkからプラン情報を取得 🚨
// TODO: Clerk Python SDK修正後に削除
// Retrieve plan information from Clerk - TO BE DELETED
async function getClerkPlan(): Promise<{
  plan: string;
  success: boolean;
  error?: string;
  source: 'has_method' | 'metadata' | 'fallback';
}> {
  try {
    // Clerk推奨のhas()メソッドを使用してプラン情報を取得
    // Use Clerk's recommended has() method to get plan information
    const { has } = await auth();

    workaroundLog('info', 'Using Clerk has() method to check plans');

    // standardプランをチェック
    // Check for standard plan
    const hasStandard = has({ plan: 'standard' });
    if (hasStandard) {
      workaroundLog('info', 'User has standard plan', { plan: 'standard' });
      return {
        plan: 'standard',
        success: true,
        source: 'has_method'
      };
    }

    // freeプランをチェック
    // Check for free plan
    const hasFree = has({ plan: 'free' });
    if (hasFree) {
      workaroundLog('info', 'User has free plan', { plan: 'free' });
      return {
        plan: 'free',
        success: true,
        source: 'has_method'
      };
    }

    // has()メソッドで見つからない場合はメタデータフォールバックを試行
    // If not found via has() method, try metadata fallback
    workaroundLog('info', 'Plan not found via has() method, trying metadata fallback');

    const { userId } = await auth();
    if (!userId) {
      throw new Error('User not authenticated');
    }

    const client = await clerkClient();
    const user = await client.users.getUser(userId);

    // メタデータから直接取得を試行
    // Try to get plan directly from metadata
    if (user.publicMetadata?.plan) {
      const planName = String(user.publicMetadata.plan).toLowerCase();
      if (planName === 'free' || planName === 'standard') {
        workaroundLog('info', 'Plan found in public metadata', { plan: planName });
        return {
          plan: planName,
          success: true,
          source: 'metadata'
        };
      }
    }

    // プライベートメタデータもチェック
    // Check private metadata as well
    if (user.privateMetadata?.plan) {
      const planName = String(user.privateMetadata.plan).toLowerCase();
      if (planName === 'free' || planName === 'standard') {
        workaroundLog('info', 'Plan found in private metadata', { plan: planName });
        return {
          plan: planName,
          success: true,
          source: 'metadata'
        };
      }
    }

    // どのプランも見つからない場合はfreeをデフォルトとする
    // If no plan is found, default to free
    workaroundLog('info', 'No specific plan found, defaulting to free');
    return {
      plan: 'free',
      success: true,
      source: 'fallback'
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    workaroundLog('error', 'Error using Clerk has() method', { error: errorMessage });

    return {
      plan: 'free',
      success: false,
      error: errorMessage,
      source: 'fallback'
    };
  }
}

// 🚨 削除予定: プラン情報を上書き 🚨
// TODO: Clerk Python SDK修正後に削除
// Override plan information - TO BE DELETED
function overridePlanInformation(
  backendResponse: AIChatUsage,
  clerkPlan: { plan: string; success: boolean; error?: string; source: 'has_method' | 'metadata' | 'fallback' }
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

    // 🚨 削除予定: プラン情報の上書き処理 🚨
    // TODO: Clerk Python SDK修正後にこのif文ブロック全体を削除
    // Temporary workaround: Plan information override process - TO BE DELETED
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
            source: 'fallback' as const
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
        // 🚨 削除予定: 暫定対応でエラーが発生した場合は元のレスポンスを返す 🚨
        // TODO: Clerk Python SDK修正後にこのcatch文も削除
        // Return original response if workaround fails - TO BE DELETED
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