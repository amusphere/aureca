/**
 * 暫定対応: Clerk JavaScript SDKを使用したプラン取得
 * TODO: Clerk Python SDKが修正されたら削除予定
 *
 * This is a temporary workaround to retrieve user plan information
 * using Clerk JavaScript SDK when the Python SDK fails to work properly.
 * This file should be deleted once the Clerk Python SDK is fixed.
 */

import { auth, clerkClient } from '@clerk/nextjs/server';

export interface ClerkPlanResult {
  plan: string;
  success: boolean;
  error?: string;
  source: 'subscription' | 'metadata' | 'fallback';
}

export class ClerkPlanHelper {
  /**
   * 暫定対応: フロントエンドでユーザープランを取得
   * Temporary workaround: Retrieve user plan information on frontend
   *
   * @returns プラン情報とメタデータ / Plan information and metadata
   */
  static async getUserPlan(): Promise<ClerkPlanResult> {
    try {
      const { userId } = auth();

      if (!userId) {
        return {
          plan: 'free',
          success: false,
          error: 'User not authenticated',
          source: 'fallback'
        };
      }

      const user = await clerkClient.users.getUser(userId);

      // 1. サブスクリプション情報から取得を試行
      // Try to get plan from subscription information
      if (user.publicMetadata?.subscription) {
        const subscription = user.publicMetadata.subscription as any;
        if (subscription.plan) {
          const planName = String(subscription.plan).toLowerCase();
          // Validate plan name
          if (planName === 'free' || planName === 'standard') {
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
      console.error('[TEMPORARY WORKAROUND] Clerk plan retrieval error:', error);

      // エラー時は"free"プランにフォールバック
      // Fallback to "free" plan on error
      return {
        plan: 'free',
        success: false,
        error: String(error),
        source: 'fallback'
      };
    }
  }

  /**
   * プラン名が有効かどうかを検証
   * Validate if plan name is valid
   *
   * @param plan プラン名 / Plan name
   * @returns 有効かどうか / Whether valid or not
   */
  static isValidPlan(plan: string): boolean {
    const validPlans = ['free', 'standard'];
    return validPlans.includes(plan.toLowerCase());
  }

  /**
   * プラン情報をログ出力用に安全な形式に変換
   * Convert plan information to safe format for logging
   *
   * @param result ClerkPlanResult
   * @returns ログ出力用オブジェクト / Object for logging
   */
  static toLogSafeFormat(result: ClerkPlanResult): Record<string, any> {
    return {
      plan: result.plan,
      success: result.success,
      source: result.source,
      hasError: !!result.error,
      // エラーの詳細は本番環境では出力しない
      // Don't output error details in production
      ...(process.env.NODE_ENV === 'development' && result.error && {
        error: result.error
      })
    };
  }
}