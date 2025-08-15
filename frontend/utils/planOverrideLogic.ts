/**
 * 暫定対応: バックエンドレスポンスのプラン情報上書きロジック
 * TODO: Clerk Python SDKが修正されたら削除予定
 *
 * Temporary workaround: Plan information override logic for backend responses
 * This file should be deleted once the Clerk Python SDK is fixed.
 */

import { AIChatUsage, PLAN_LIMITS, SubscriptionPlan } from '@/types/AIChatUsage';
import { ClerkPlanResult } from './clerkPlanHelper';

export interface PlanOverrideResult {
  data: AIChatUsage;
  wasOverridden: boolean;
  originalPlan?: string;
  newPlan?: string;
  error?: string;
}

export class PlanOverrideLogic {
  /**
   * 暫定対応: バックエンドレスポンスのプラン情報を上書き
   * Temporary workaround: Override plan information in backend response
   *
   * @param backendResponse バックエンドからのレスポンス / Backend response
   * @param clerkPlan フロントエンドで取得したプラン情報 / Plan info from frontend
   * @returns 上書き後のレスポンス / Response after override
   */
  static overridePlanInformation(
    backendResponse: AIChatUsage,
    clerkPlan: ClerkPlanResult
  ): PlanOverrideResult {
    try {
      // フロントエンドでのプラン取得が失敗した場合は上書きしない
      // Don't override if frontend plan retrieval failed
      if (!clerkPlan.success) {
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
      if (!this.isValidPlan(newPlan)) {
        console.warn('[TEMPORARY WORKAROUND] Invalid plan name from Clerk:', newPlan);
        return {
          data: backendResponse,
          wasOverridden: false,
          error: `Invalid plan name: ${newPlan}`
        };
      }

      // プランが同じ場合は上書き不要
      // No override needed if plans are the same
      if (originalPlan === newPlan) {
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

      const overriddenResponse: AIChatUsage = {
        ...backendResponse,
        plan_name: newPlan,
        daily_limit: newDailyLimit,
        remaining_count: newRemainingCount,
        can_use_chat: newCanUseChat
      };

      console.log(`[TEMPORARY WORKAROUND] Plan overridden: ${originalPlan} → ${newPlan}`);

      return {
        data: overriddenResponse,
        wasOverridden: true,
        originalPlan,
        newPlan
      };

    } catch (error) {
      console.error('[TEMPORARY WORKAROUND] Plan override error:', error);
      return {
        data: backendResponse,
        wasOverridden: false,
        error: String(error)
      };
    }
  }

  /**
   * プラン変更が有効かどうかを検証
   * Validate if plan change is valid
   *
   * @param originalPlan 元のプラン / Original plan
   * @param newPlan 新しいプラン / New plan
   * @returns 有効な変更かどうか / Whether the change is valid
   */
  static isValidPlanChange(originalPlan?: string, newPlan?: string): boolean {
    const validPlans = ['free', 'standard'];
    return validPlans.includes(originalPlan || '') && validPlans.includes(newPlan || '');
  }

  /**
   * プラン名が有効かどうかを検証
   * Validate if plan name is valid
   *
   * @param plan プラン名 / Plan name
   * @returns 有効かどうか / Whether valid
   */
  private static isValidPlan(plan: string): plan is SubscriptionPlan {
    return plan === 'free' || plan === 'standard';
  }

  /**
   * 上書き結果をログ出力用に安全な形式に変換
   * Convert override result to safe format for logging
   *
   * @param result PlanOverrideResult
   * @returns ログ出力用オブジェクト / Object for logging
   */
  static toLogSafeFormat(result: PlanOverrideResult): Record<string, any> {
    return {
      wasOverridden: result.wasOverridden,
      originalPlan: result.originalPlan,
      newPlan: result.newPlan,
      hasError: !!result.error,
      // エラーの詳細は本番環境では出力しない
      // Don't output error details in production
      ...(process.env.NODE_ENV === 'development' && result.error && {
        error: result.error
      })
    };
  }
}