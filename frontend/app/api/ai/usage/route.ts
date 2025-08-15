import { AIChatUsage, AIChatUsageError } from "@/types/AIChatUsage";
import { apiGet } from "@/utils/api";
import { NextResponse } from "next/server";

// 暫定対応: Clerk JavaScript SDKでのプラン取得
// TODO: Clerk Python SDKが修正されたら以下のimportを削除
// Temporary workaround: Plan retrieval using Clerk JavaScript SDK
// TODO: Remove these imports once Clerk Python SDK is fixed
import { ClerkPlanHelper } from "@/utils/clerkPlanHelper";
import { PlanOverrideLogic } from "@/utils/planOverrideLogic";

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
    // Note: Remove /api prefix since API_BASE_URL already includes it
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
        console.log('[TEMPORARY WORKAROUND] Starting plan override process');

        // フロントエンドでプラン情報を取得
        // Retrieve plan information on frontend
        const clerkPlan = await ClerkPlanHelper.getUserPlan();

        console.log('[TEMPORARY WORKAROUND] Clerk plan retrieved:',
          ClerkPlanHelper.toLogSafeFormat(clerkPlan));

        // プラン情報でレスポンスを上書き
        // Override response with plan information
        const overrideResult = PlanOverrideLogic.overridePlanInformation(
          response.data,
          clerkPlan
        );

        if (overrideResult.wasOverridden) {
          console.log('[TEMPORARY WORKAROUND] Plan information overridden:',
            PlanOverrideLogic.toLogSafeFormat(overrideResult));
        }

        return NextResponse.json(overrideResult.data);

      } catch (workaroundError) {
        // 暫定対応でエラーが発生した場合は元のレスポンスを返す
        // Return original response if workaround fails
        console.error('[TEMPORARY WORKAROUND] Workaround failed, using original response:', workaroundError);
        return NextResponse.json(response.data);
      }
    }

    // Success response (fallback)
    return NextResponse.json(response.data);

  } catch (error) {
    // 既存のエラーハンドリング
    // Existing error handling
    console.error('AI Usage API Error:', error);

    const errorResponse: AIChatUsageError = {
      error: 'システムエラーが発生しました',
      error_code: 'SYSTEM_ERROR',
      remaining_count: 0,
      reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}