/**
 * アクセシビリティ機能を管理するカスタムフック
 */

import {
  announceToScreenReader,
  auditAccessibility,
  enableKeyboardNavigation
} from '@/utils/accessibility';
import { useCallback, useEffect } from 'react';

export function useAccessibility() {
  // キーボードナビゲーションの初期化
  useEffect(() => {
    enableKeyboardNavigation();
  }, []);

  // スクリーンリーダーへのアナウンス
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announceToScreenReader(message, priority);
  }, []);

  // アクセシビリティ監査の実行
  const runAudit = useCallback(() => {
    const results = auditAccessibility();

    // 開発環境でのみコンソールに出力
    if (process.env.NODE_ENV === 'development') {
      console.group('アクセシビリティ監査結果');

      if (results.contrastIssues.length > 0) {
        console.warn('コントラスト問題:', results.contrastIssues);
      }

      if (results.focusIssues.length > 0) {
        console.warn('フォーカス問題:', results.focusIssues);
      }

      if (results.ariaIssues.length > 0) {
        console.warn('ARIA問題:', results.ariaIssues);
      }

      if (results.keyboardIssues.length > 0) {
        console.warn('キーボードアクセシビリティ問題:', results.keyboardIssues);
      }

      const totalIssues = Object.values(results).reduce((sum, issues) => sum + issues.length, 0);
      if (totalIssues === 0) {
        console.log('✅ アクセシビリティ問題は見つかりませんでした');
      } else {
        console.log(`⚠️ ${totalIssues}件のアクセシビリティ問題が見つかりました`);
      }

      console.groupEnd();
    }

    return results;
  }, []);

  return {
    announce,
    runAudit
  };
}
