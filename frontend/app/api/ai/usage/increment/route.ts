import { AIChatUsage, AIChatUsageError } from "@/types/AIChatUsage";
import { apiPost } from "@/utils/api";
import { NextResponse } from "next/server";

/**
 * POST /api/ai/usage/increment
 * Increment AI Chat usage count for the authenticated user
 * This is typically called after successful AI chat processing
 *
 * Returns:
 * - 200: Updated AIChatUsage object
 * - 403: Plan restriction error
 * - 429: Usage limit exceeded error
 * - 500: System error
 */
export async function POST(): Promise<NextResponse> {
  try {
    // Call backend API to increment usage
    // Note: Remove /api prefix since API_BASE_URL already includes it
    const response = await apiPost<AIChatUsage>('/ai/usage/increment');

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

    // Success response with updated usage stats
    return NextResponse.json(response.data);

  } catch (error) {
    // Catch any unexpected errors
    console.error('AI Usage Increment API Error:', error);

    const errorResponse: AIChatUsageError = {
      error: 'システムエラーが発生しました',
      errorCode: 'SYSTEM_ERROR',
      remainingCount: 0,
      resetTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}