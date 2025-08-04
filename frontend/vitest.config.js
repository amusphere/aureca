import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    testTimeout: 10000,
    // メモリ使用量を最適化
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    // テストファイルのパターンを指定
    include: ['tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    // 大きなテストファイルを除外（メモリ問題があるため）
    exclude: ['**/node_modules/**', '**/dist/**', 'tests/hooks/useAIChatUsage.test.ts'],
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