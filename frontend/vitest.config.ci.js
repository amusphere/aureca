import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    testTimeout: 30000, // CI環境では長めのタイムアウト
    // CI環境では安定性重視
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    // テストファイルのパターンを指定
    include: ['tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    // 大きなテストファイルを除外（メモリ問題があるため）
    exclude: ['**/node_modules/**', '**/dist/**', '**/coverage/**'],
    // CI環境での安定性設定
    isolate: true, // テスト間の完全分離
    passWithNoTests: true,
    // 非同期処理のクリーンアップ（CI環境では長め）
    teardownTimeout: 30000,
    hookTimeout: 30000,
    // ファイル変更監視の最適化
    watchExclude: ['**/node_modules/**', '**/dist/**', '**/coverage/**'],
    // CI環境では詳細なレポート
    reporter: ['verbose', 'junit'],
    outputFile: {
      junit: './test-results/junit.xml'
    },
    // カバレッジ設定
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: 'coverage',
      include: [
        'app/**/*.{js,ts,jsx,tsx}',
        'components/**/*.{js,ts,jsx,tsx}',
        'utils/**/*.{js,ts,jsx,tsx}',
        'types/**/*.{js,ts,jsx,tsx}'
      ],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.{js,ts}',
        'next.config.ts',
        'tailwind.config.js',
        'postcss.config.mjs'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), './'),
    },
  },
})