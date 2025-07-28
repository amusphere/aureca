/**
 * デモ環境かどうかを判定するユーティリティ関数
 */
export function isDemoEnvironment(): boolean {
  if (typeof window === 'undefined') return false;
  return window.location.pathname.startsWith('/demo');
}

/**
 * デモ環境でのAI機能アクセス制限メッセージ
 */
export const DEMO_AI_RESTRICTION_MESSAGE = {
  title: 'AI機能はデモでは利用できません',
  description: 'AI アシスタント機能は本格利用でのみご利用いただけます。登録して全機能をお試しください。',
  action: '本格利用を開始'
};

/**
 * デモ環境での機能制限チェック
 */
export function checkDemoFeatureAccess(feature: 'ai_chat' | 'integrations' | 'advanced_features'): {
  allowed: boolean;
  message?: string;
} {
  if (!isDemoEnvironment()) {
    return { allowed: true };
  }

  switch (feature) {
    case 'ai_chat':
      return {
        allowed: false,
        message: 'AI チャット機能は本格利用でのみご利用いただけます'
      };
    case 'integrations':
      return {
        allowed: false,
        message: '外部サービス連携は本格利用でのみご利用いただけます'
      };
    case 'advanced_features':
      return {
        allowed: false,
        message: '高度な機能は本格利用でのみご利用いただけます'
      };
    default:
      return { allowed: true };
  }
}