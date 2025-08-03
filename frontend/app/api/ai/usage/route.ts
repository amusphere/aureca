import { apiGet } from "@/utils/api";
import { AIChatUsage, AIChatUsageError } from "@/types/AIChatUsage";
import { NextResponse } from "next/server";

/**
 * GET /api/ai/usage
 * Fetch AI Chat usage information for the authenticated user
 *
 * Returns:
 * - 200: AIChatUsage object with current usage stats
 * - 403: Plan restriction error (free plan users)
 * - 429: Usage limit exceeded error
 * - 500: System error
 */
export async function GET(): Promise<NextResponse> {
  try {
    // Call backend API through server-side proxy
    const response = await apiGet<AIChatUsage>('/api/ai/usage');

    if (response.error) {
      // Handle different types of errors from backend
      const status = response.error.status || 500;

      // For usage-related errors (403, 429), return the error details
      if (status === 403 || status === 429) {
        const errorResponse: AIChatUsageError = {
          error: response.error.message,
          errorCode: response.error.details?.error_code || 'SYSTEM_ERROR',
          remainingCount: response.error.details?.remaining_count || 0,
          resetTime: response.error.details?.reset_time || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        };

        return NextResponse.json(errorResponse, { status });
      }

      // For other errors, return generic error response
      return NextResponse.json(
        {
          error: response.error.message || 'システムエラーが発生しました',
          errorCode: 'SYSTEM_ERROR',
          remainingCount: 0,
          resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        } as AIChatUsageError,
        { status }
      );
    }

    // Success response
    return NextResponse.json(response.data);

  } catch (error) {
    // Catch any unexpected errors
    console.error('AI Usage API Error:', error);

    const errorResponse: AIChatUsageError = {
      error: 'システムエラーが発生しました',
      errorCode: 'SYSTEM_ERROR',
      remainingCount: 0,
      resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}