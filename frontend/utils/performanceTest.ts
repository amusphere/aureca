/**
 * CSS変更のパフォーマンステストユーティリティ
 */

interface PerformanceMetrics {
  renderTime: number;
  paintTime: number;
  layoutTime: number;
  animationFrameRate: number;
  memoryUsage?: number;
}

// レンダリングパフォーマンスを測定
export function measureRenderPerformance(): Promise<PerformanceMetrics> {
  return new Promise((resolve) => {
    const startTime = performance.now();
    let paintTime = 0;
    let layoutTime = 0;
    let frameCount = 0;

    // Paint timing を測定
    const paintObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'paint') {
          paintTime = entry.startTime;
        }
      });
    });
    paintObserver.observe({ entryTypes: ['paint'] });

    // Layout shift を測定
    const layoutObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'layout-shift') {
          layoutTime += entry.startTime;
        }
      });
    });
    layoutObserver.observe({ entryTypes: ['layout-shift'] });

    // フレームレートを測定
    const measureFrameRate = () => {
      const currentTime = performance.now();
      frameCount++;

      if (currentTime - startTime >= 1000) {
        const renderTime = performance.now() - startTime;
        const animationFrameRate = frameCount;

        // メモリ使用量を取得（可能な場合）
        const memoryUsage = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize;

        paintObserver.disconnect();
        layoutObserver.disconnect();

        resolve({
          renderTime,
          paintTime,
          layoutTime,
          animationFrameRate,
          memoryUsage
        });
      } else {
        requestAnimationFrame(measureFrameRate);
      }
    };

    requestAnimationFrame(measureFrameRate);
  });
}

// CSS アニメーションのパフォーマンスを測定
export function measureAnimationPerformance(element: HTMLElement, animationClass: string): Promise<number> {
  return new Promise((resolve) => {
    const startTime = performance.now();
    let frameCount = 0;

    element.classList.add(animationClass);

    const measureFrame = () => {
      frameCount++;

      // アニメーション終了を検出
      const animationEndHandler = () => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        const fps = frameCount / (duration / 1000);

        element.classList.remove(animationClass);
        element.removeEventListener('animationend', animationEndHandler);

        resolve(fps);
      };

      element.addEventListener('animationend', animationEndHandler, { once: true });

      // フレーム測定を継続
      if (element.classList.contains(animationClass)) {
        requestAnimationFrame(measureFrame);
      }
    };

    requestAnimationFrame(measureFrame);
  });
}

// CSS セレクターの複雑さを分析
export function analyzeCSSComplexity(): {
  totalRules: number;
  complexSelectors: string[];
  recommendations: string[];
} {
  const styleSheets = Array.from(document.styleSheets);
  let totalRules = 0;
  const complexSelectors: string[] = [];
  const recommendations: string[] = [];

  styleSheets.forEach((sheet) => {
    try {
      const rules = Array.from(sheet.cssRules || []);
      totalRules += rules.length;

      rules.forEach((rule) => {
        if (rule instanceof CSSStyleRule) {
          const selector = rule.selectorText;

          // 複雑なセレクターを検出
          const selectorComplexity = (selector.match(/[>+~\s]/g) || []).length;
          if (selectorComplexity > 3) {
            complexSelectors.push(selector);
          }

          // パフォーマンスに影響する可能性のあるプロパティをチェック
          const style = rule.style;
          if (style.boxShadow && style.boxShadow !== 'none') {
            if (!style.willChange) {
              recommendations.push(`${selector}: box-shadowを使用する場合はwill-changeの追加を検討してください`);
            }
          }

          if (style.transform && !style.willChange) {
            recommendations.push(`${selector}: transformを使用する場合はwill-changeの追加を検討してください`);
          }
        }
      });
    } catch (error) {
      // Cross-origin stylesheets などでアクセスできない場合
      console.warn('スタイルシートにアクセスできません:', error);
    }
  });

  return {
    totalRules,
    complexSelectors,
    recommendations
  };
}

// レスポンシブデザインのテスト
export function testResponsiveDesign(): Promise<{
  breakpoints: Array<{
    width: number;
    issues: string[];
  }>;
}> {
  return new Promise((resolve) => {
    const breakpoints = [320, 640, 768, 1024, 1280, 1920];
    const results: Array<{ width: number; issues: string[] }> = [];
    let currentIndex = 0;

    const testBreakpoint = (width: number) => {
      const issues: string[] = [];

      // ビューポートサイズを変更
      const originalWidth = window.innerWidth;
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width
      });

      // メディアクエリの変更をトリガー
      window.dispatchEvent(new Event('resize'));

      setTimeout(() => {
        // 横スクロールの検出
        if (document.body.scrollWidth > width) {
          issues.push('横スクロールが発生しています');
        }

        // 重なり要素の検出
        const elements = document.querySelectorAll('*');
        elements.forEach((element) => {
          const rect = element.getBoundingClientRect();
          if (rect.width > width) {
            issues.push(`要素がビューポートからはみ出しています: ${element.tagName}`);
          }
        });

        // テキストの可読性チェック
        const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
        textElements.forEach((element) => {
          const styles = window.getComputedStyle(element);
          const fontSize = parseFloat(styles.fontSize);
          if (fontSize < 14 && width <= 640) {
            issues.push('モバイルでテキストサイズが小さすぎます');
          }
        });

        results.push({ width, issues });

        // 次のブレークポイントをテスト
        currentIndex++;
        if (currentIndex < breakpoints.length) {
          testBreakpoint(breakpoints[currentIndex]);
        } else {
          // 元のサイズに戻す
          Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: originalWidth
          });
          window.dispatchEvent(new Event('resize'));

          resolve({ breakpoints: results });
        }
      }, 100);
    };

    testBreakpoint(breakpoints[0]);
  });
}

// パフォーマンス監視の開始
export function startPerformanceMonitoring(): () => void {
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    entries.forEach((entry) => {
      if (entry.entryType === 'measure') {
        console.log(`Performance: ${entry.name} took ${entry.duration}ms`);
      }

      if (entry.entryType === 'navigation') {
        const navEntry = entry as PerformanceNavigationTiming;
        console.log('Navigation timing:', {
          domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
          loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
          firstPaint: navEntry.responseEnd - navEntry.requestStart
        });
      }
    });
  });

  observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] });

  return () => observer.disconnect();
}

// CSS最適化の提案
export function suggestCSSOptimizations(): string[] {
  const suggestions: string[] = [];

  // 未使用のCSSルールを検出（簡略化）
  const allElements = document.querySelectorAll('*');
  const usedClasses = new Set<string>();

  allElements.forEach((element) => {
    element.classList.forEach((className) => {
      usedClasses.add(className);
    });
  });

  // 重複するスタイルの検出
  const styleMap = new Map<string, string[]>();
  document.querySelectorAll('[style]').forEach((element) => {
    const style = (element as HTMLElement).style.cssText;
    if (styleMap.has(style)) {
      styleMap.get(style)!.push(element.tagName);
    } else {
      styleMap.set(style, [element.tagName]);
    }
  });

  styleMap.forEach((elements, style) => {
    if (elements.length > 1) {
      suggestions.push(`重複するインラインスタイルをCSSクラスに統合することを検討してください: ${style}`);
    }
  });

  // 高コストなプロパティの使用チェック
  const expensiveProperties = ['box-shadow', 'border-radius', 'opacity', 'transform'];
  const styleSheets = Array.from(document.styleSheets);

  styleSheets.forEach((sheet) => {
    try {
      const rules = Array.from(sheet.cssRules || []);
      rules.forEach((rule) => {
        if (rule instanceof CSSStyleRule) {
          expensiveProperties.forEach((prop) => {
            if (rule.style.getPropertyValue(prop)) {
              suggestions.push(`${rule.selectorText}で${prop}を使用しています。will-changeの追加を検討してください`);
            }
          });
        }
      });
    } catch (error) {
      // アクセスできないスタイルシートをスキップ
      console.warn('スタイルシートにアクセスできません:', error);
    }
  });

  return suggestions;
}

// 総合的なパフォーマンステスト
export async function runComprehensivePerformanceTest(): Promise<{
  renderMetrics: PerformanceMetrics;
  cssComplexity: ReturnType<typeof analyzeCSSComplexity>;
  responsiveIssues: Awaited<ReturnType<typeof testResponsiveDesign>>;
  optimizationSuggestions: string[];
}> {
  console.log('パフォーマンステストを開始します...');

  const [renderMetrics, responsiveIssues] = await Promise.all([
    measureRenderPerformance(),
    testResponsiveDesign()
  ]);

  const cssComplexity = analyzeCSSComplexity();
  const optimizationSuggestions = suggestCSSOptimizations();

  console.log('パフォーマンステスト完了');

  return {
    renderMetrics,
    cssComplexity,
    responsiveIssues,
    optimizationSuggestions
  };
}