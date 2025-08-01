/**
 * アクセシビリティユーティリティ関数
 * WCAG AA準拠の確認とキーボードナビゲーション支援
 */

import { TaskPriority } from "@/types/Task";

// カラーコントラスト比を計算する関数
export function calculateContrastRatio(color1: string, color2: string): number {
  const getLuminance = (color: string): number => {
    // oklch形式の色をRGBに変換して輝度を計算
    // 簡略化された実装
    const rgb = parseOklchToRgb(color);
    const [r, g, b] = rgb.map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const lum1 = getLuminance(color1);
  const lum2 = getLuminance(color2);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);

  return (brightest + 0.05) / (darkest + 0.05);
}

// oklch形式をRGBに変換（改良版）
function parseOklchToRgb(oklch: string): [number, number, number] {
  // 実際の実装では、oklch-to-rgb変換ライブラリを使用することを推奨
  // ここでは改良された実装
  const match = oklch.match(/oklch\(([\d.]+)\s+([\d.]+)\s+([\d.]+)\)/);
  if (!match) return [128, 128, 128]; // デフォルト値

  const [, l, chroma, hue] = match.map(Number);

  // 簡略化されたOKLCH to RGB変換
  // 実際の変換はより複雑ですが、コントラスト計算には十分な精度
  const lightness = l;
  const a = chroma * Math.cos((hue * Math.PI) / 180);
  const b = chroma * Math.sin((hue * Math.PI) / 180);

  // 線形RGB近似
  const r = Math.max(0, Math.min(255, Math.round((lightness + 0.3963377774 * a + 0.2158037573 * b) * 255)));
  const g = Math.max(0, Math.min(255, Math.round((lightness - 0.1055613458 * a - 0.0638541728 * b) * 255)));
  const blue = Math.max(0, Math.min(255, Math.round((lightness - 0.0894841775 * a - 1.2914855480 * b) * 255)));

  return [r, g, blue];
}

// WCAG AA準拠チェック
export function checkWCAGCompliance(foreground: string, background: string): {
  ratio: number;
  passAA: boolean;
  passAAA: boolean;
  level: 'AA' | 'AAA' | 'FAIL';
} {
  const ratio = calculateContrastRatio(foreground, background);
  const passAA = ratio >= 4.5;
  const passAAA = ratio >= 7;

  return {
    ratio,
    passAA,
    passAAA,
    level: passAAA ? 'AAA' : passAA ? 'AA' : 'FAIL'
  };
}

// キーボードナビゲーション支援
export function enableKeyboardNavigation(): void {
  // キーボード使用を検出
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      document.body.setAttribute('data-keyboard-navigation', 'true');
    }
  });

  // マウス使用を検出
  document.addEventListener('mousedown', () => {
    document.body.removeAttribute('data-keyboard-navigation');
  });

  // Escキーでフォーカス解除
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const activeElement = document.activeElement as HTMLElement;
      if (activeElement && activeElement.blur) {
        activeElement.blur();
      }
    }
  });
}

// スクリーンリーダー用のアナウンス
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcer = document.getElementById('sr-announcements');
  if (announcer) {
    announcer.setAttribute('aria-live', priority);
    announcer.textContent = message;

    // メッセージをクリア
    setTimeout(() => {
      announcer.textContent = '';
    }, 1000);
  }
}

// フォーカス管理
export function manageFocus(element: HTMLElement | null): void {
  if (!element) return;

  element.focus();

  // フォーカスが見えるようにスクロール
  element.scrollIntoView({
    behavior: 'smooth',
    block: 'nearest',
    inline: 'nearest'
  });
}

// アクセシブルなモーダル管理
export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as NodeListOf<HTMLElement>;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  container.addEventListener('keydown', handleTabKey);

  // 最初の要素にフォーカス
  firstElement?.focus();

  // クリーンアップ関数を返す
  return () => {
    container.removeEventListener('keydown', handleTabKey);
  };
}

// 色覚異常対応チェック
export function checkColorBlindnessSupport(): boolean {
  // 色だけに依存しない情報伝達ができているかチェック
  const colorOnlyElements = document.querySelectorAll('[data-color-only]');
  return colorOnlyElements.length === 0;
}

// アニメーション設定の確認
export function respectsMotionPreferences(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// アクセシビリティ監査
export function auditAccessibility(): {
  contrastIssues: Array<{ element: Element; issue: string }>;
  focusIssues: Array<{ element: Element; issue: string }>;
  ariaIssues: Array<{ element: Element; issue: string }>;
  keyboardIssues: Array<{ element: Element; issue: string }>;
} {
  const issues = {
    contrastIssues: [] as Array<{ element: Element; issue: string }>,
    focusIssues: [] as Array<{ element: Element; issue: string }>,
    ariaIssues: [] as Array<{ element: Element; issue: string }>,
    keyboardIssues: [] as Array<{ element: Element; issue: string }>
  };

  // インタラクティブ要素のチェック
  const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]');

  interactiveElements.forEach(element => {
    // フォーカス可能性チェック
    const tabIndex = element.getAttribute('tabindex');
    if (tabIndex === '-1' && element.tagName !== 'DIV') {
      issues.focusIssues.push({
        element,
        issue: 'インタラクティブ要素がフォーカス不可能です'
      });
    }

    // ARIA属性チェック
    const role = element.getAttribute('role');
    const ariaLabel = element.getAttribute('aria-label');
    const ariaLabelledby = element.getAttribute('aria-labelledby');

    if (element.tagName === 'BUTTON' && !element.textContent?.trim() && !ariaLabel && !ariaLabelledby) {
      issues.ariaIssues.push({
        element,
        issue: 'ボタンにアクセシブルな名前がありません'
      });
    }

    // キーボードアクセシビリティチェック
    if (element.tagName === 'DIV' && (role === 'button' || (element as HTMLElement).onclick)) {
      if (!element.hasAttribute('tabindex')) {
        issues.keyboardIssues.push({
          element,
          issue: 'クリック可能な要素がキーボードでアクセスできません'
        });
      }
    }
  });

  return issues;
}

// パフォーマンス最適化のためのIntersection Observer
export function createPerformantObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options?: IntersectionObserverInit
): IntersectionObserver {
  return new IntersectionObserver(callback, {
    rootMargin: '50px',
    threshold: 0.1,
    ...options
  });
}

// レスポンシブデザインのブレークポイント検出
export function getCurrentBreakpoint(): 'mobile' | 'tablet' | 'desktop' {
  const width = window.innerWidth;
  if (width <= 640) return 'mobile';
  if (width <= 768) return 'tablet';
  return 'desktop';
}

// メディアクエリの変更を監視
export function watchBreakpointChanges(callback: (breakpoint: string) => void): () => void {
  const mobileQuery = window.matchMedia('(max-width: 640px)');
  const tabletQuery = window.matchMedia('(min-width: 641px) and (max-width: 768px)');

  const handleChange = () => {
    callback(getCurrentBreakpoint());
  };

  mobileQuery.addEventListener('change', handleChange);
  tabletQuery.addEventListener('change', handleChange);

  return () => {
    mobileQuery.removeEventListener('change', handleChange);
    tabletQuery.removeEventListener('change', handleChange);
  };
}

// === 優先度関連のアクセシビリティ機能 ===

/**
 * 優先度に基づいてアクセシブルな説明文を生成
 */
export function getPriorityDescription(priority?: TaskPriority): string {
  if (!priority) return "優先度未設定";

  switch (priority) {
    case 1:
      return "高優先度 - 緊急度が高く、早急な対応が必要なタスクです";
    case 2:
      return "中優先度 - 重要なタスクですが、時間に余裕があります";
    case 3:
      return "低優先度 - 時間があるときに対応すれば良いタスクです";
    default:
      return "優先度未設定";
  }
}

/**
 * 優先度に基づいてアクセシブルなラベルを生成
 */
export function getPriorityAriaLabel(priority?: TaskPriority): string {
  if (!priority) return "優先度未設定";

  switch (priority) {
    case 1:
      return "高優先度タスク";
    case 2:
      return "中優先度タスク";
    case 3:
      return "低優先度タスク";
    default:
      return "優先度未設定";
  }
}

/**
 * 優先度変更をスクリーンリーダーにアナウンス
 */
export function announcePriorityChange(priority?: TaskPriority, taskTitle?: string): void {
  const priorityText = getPriorityDescription(priority);
  const message = taskTitle
    ? `タスク「${taskTitle}」の優先度を${priorityText}に変更しました`
    : `優先度を${priorityText}に変更しました`;

  announceToScreenReader(message, 'polite');
}

/**
 * 優先度選択のキーボードショートカット
 */
export function handlePriorityKeyboardShortcuts(
  event: KeyboardEvent,
  onPriorityChange: (priority: TaskPriority | undefined) => void
): boolean {
  // Ctrl/Cmd + 数字キーで優先度を設定
  if ((event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey) {
    switch (event.key) {
      case '1':
        event.preventDefault();
        onPriorityChange(1);
        announceToScreenReader('高優先度に設定しました', 'polite');
        return true;
      case '2':
        event.preventDefault();
        onPriorityChange(2);
        announceToScreenReader('中優先度に設定しました', 'polite');
        return true;
      case '3':
        event.preventDefault();
        onPriorityChange(3);
        announceToScreenReader('低優先度に設定しました', 'polite');
        return true;
      case '0':
        event.preventDefault();
        onPriorityChange(undefined);
        announceToScreenReader('優先度を未設定にしました', 'polite');
        return true;
    }
  }
  return false;
}

/**
 * 優先度バッジの色がアクセシブルかチェック
 */
export function validatePriorityColors(): {
  high: boolean;
  medium: boolean;
  low: boolean;
} {
  const results = {
    high: false,
    medium: false,
    low: false
  };

  // 実際のDOM要素から色を取得してチェック
  if (typeof window !== 'undefined') {
    const testContainer = document.createElement('div');
    testContainer.style.position = 'absolute';
    testContainer.style.top = '-9999px';
    document.body.appendChild(testContainer);

    try {
      // 高優先度バッジのテスト
      testContainer.innerHTML = '<span class="priority-high-badge">高</span>';
      const highElement = testContainer.querySelector('.priority-high-badge') as HTMLElement;
      if (highElement) {
        const style = window.getComputedStyle(highElement);
        const { passAA } = checkWCAGCompliance(style.color, style.backgroundColor);
        results.high = passAA;
      }

      // 中優先度バッジのテスト
      testContainer.innerHTML = '<span class="priority-medium-badge">中</span>';
      const mediumElement = testContainer.querySelector('.priority-medium-badge') as HTMLElement;
      if (mediumElement) {
        const style = window.getComputedStyle(mediumElement);
        const { passAA } = checkWCAGCompliance(style.color, style.backgroundColor);
        results.medium = passAA;
      }

      // 低優先度バッジのテスト
      testContainer.innerHTML = '<span class="priority-low-badge">低</span>';
      const lowElement = testContainer.querySelector('.priority-low-badge') as HTMLElement;
      if (lowElement) {
        const style = window.getComputedStyle(lowElement);
        const { passAA } = checkWCAGCompliance(style.color, style.backgroundColor);
        results.low = passAA;
      }
    } finally {
      document.body.removeChild(testContainer);
    }
  }

  return results;
}