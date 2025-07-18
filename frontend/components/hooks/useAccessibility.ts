/**
 * アクセシビリティ機能を管理するカスタムフック
 */

import {
  announceToScreenReader,
  auditAccessibility,
  checkWCAGCompliance,
  enableKeyboardNavigation,
  getCurrentBreakpoint,
  manageFocus,
  trapFocus,
  watchBreakpointChanges
} from '@/utils/accessibility';
import { startPerformanceMonitoring } from '@/utils/performanceTest';
import { useCallback, useEffect, useState } from 'react';

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

// レスポンシブデザイン対応のフック
export function useResponsiveDesign() {
  const [breakpoint, setBreakpoint] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');

  useEffect(() => {
    // 初期ブレークポイントを設定
    setBreakpoint(getCurrentBreakpoint());

    // ブレークポイントの変更を監視
    const cleanup = watchBreakpointChanges((newBreakpoint) => {
      setBreakpoint(newBreakpoint as 'mobile' | 'tablet' | 'desktop');
    });

    return cleanup;
  }, []);

  return {
    breakpoint,
    isMobile: breakpoint === 'mobile',
    isTablet: breakpoint === 'tablet',
    isDesktop: breakpoint === 'desktop'
  };
}

// パフォーマンス監視のフック
export function usePerformanceMonitoring() {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      const stopMonitoring = startPerformanceMonitoring();
      return stopMonitoring;
    }
  }, []);

  const measureComponentRender = useCallback((componentName: string) => {
    if (process.env.NODE_ENV === 'development') {
      performance.mark(`${componentName}-start`);

      return () => {
        performance.mark(`${componentName}-end`);
        performance.measure(
          `${componentName}-render`,
          `${componentName}-start`,
          `${componentName}-end`
        );
      };
    }

    return () => { }; // 本番環境では何もしない
  }, []);

  return {
    measureComponentRender
  };
}

// WCAG準拠チェックのフック
export function useWCAGCompliance() {
  const checkColorContrast = useCallback((foreground: string, background: string) => {
    return checkWCAGCompliance(foreground, background);
  }, []);

  const auditPageAccessibility = useCallback(() => {
    return auditAccessibility();
  }, []);

  return {
    checkColorContrast,
    auditPageAccessibility
  };
}

// フォーカス管理のフック
export function useFocusManagement() {
  const trapFocusInContainer = useCallback((container: HTMLElement) => {
    return trapFocus(container);
  }, []);

  const manageFocusElement = useCallback((element: HTMLElement | null) => {
    manageFocus(element);
  }, []);

  return {
    trapFocus: trapFocusInContainer,
    manageFocus: manageFocusElement
  };
}