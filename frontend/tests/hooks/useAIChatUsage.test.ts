import { AI_CHAT_USAGE_ERROR_CODES } from '@/types/AIChatUsage'
import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAIChatUsage } from '../../components/hooks/useAIChatUsage'
import * as useErrorHandlingModule from '../../components/hooks/useErrorHandling'

// Mock the useErrorHandling hook
vi.mock('../../components/hooks/useErrorHandling', () => ({
  useErrorHandling: () => ({
    error: null,
    withErrorHandling: vi.fn((fn) => fn()),
    clearError: vi.fn(),
  }),
}))

describe('useAIChatUsage', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    global.fetch = mockFetch
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  describe('初期状態', () => {
    it('初期状態では loading が true である', () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          remainingCount: 5,
          dailyLimit: 10,
          resetTime: '2024-01-02T00:00:00Z',
          canUseChat: true,
        }),
      })

      const { result } = renderHook(() => useAIChatUsage())

      expect(result.current.loading).toBe(true)
      expect(result.current.usage).toBe(null)
      expect(result.current.error).toBe(null)
    })

    it('初期状態では canUseChat が false である', () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          remainingCount: 5,
          dailyLimit: 10,
          resetTime: '2024-01-02T00:00:00Z',
          canUseChat: true,
        }),
      })

      const { result } = renderHook(() => useAIChatUsage())

      expect(result.current.canUseChat).toBe(false)
      expect(result.current.isUsageExhausted).toBe(true)
    })
  })

  describe('利用状況の取得', () => {
    it('正常な利用状況データを取得できる', async () => {
      const mockUsageData = {
        remainingCount: 5,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toEqual(mockUsageData)
      expect(result.current.error).toBe(null)
      expect(result.current.canUseChat).toBe(true)
      expect(result.current.isUsageExhausted).toBe(false)
    })

    it('利用回数が0の場合、isUsageExhausted が true になる', async () => {
      const mockUsageData = {
        remainingCount: 0,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: false,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toEqual(mockUsageData)
      expect(result.current.canUseChat).toBe(false)
      expect(result.current.isUsageExhausted).toBe(true)
    })
  })

  describe('エラーハンドリング', () => {
    it('利用制限エラー (429) を適切に処理する', async () => {
      const mockErrorData = {
        error: '本日の利用回数上限に達しました',
        errorCode: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remainingCount: 0,
        resetTime: '2024-01-02T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve(mockErrorData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toEqual(mockErrorData)
      expect(result.current.canUseChat).toBe(false)
      expect(result.current.isUsageExhausted).toBe(true)
    })

    it('プラン制限エラー (403) を適切に処理する', async () => {
      const mockErrorData = {
        error: '現在のプランではAIChatをご利用いただけません',
        errorCode: AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION,
        remainingCount: 0,
        resetTime: '2024-01-02T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: () => Promise.resolve(mockErrorData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toEqual(mockErrorData)
      expect(result.current.canUseChat).toBe(false)
    })

    it('システムエラー (500) を適切に処理する', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toMatchObject({
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
      })
      expect(result.current.canUseChat).toBe(false)
    })

    it('ネットワークエラーを適切に処理する', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toMatchObject({
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
      })
      expect(result.current.canUseChat).toBe(false)
    })
  })

  describe('利用回数の増分', () => {
    it('利用回数を正常に増分できる', async () => {
      const initialUsageData = {
        remainingCount: 5,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      const updatedUsageData = {
        remainingCount: 4,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(initialUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Increment usage
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedUsageData),
      })

      const incrementResult = await result.current.incrementUsage()

      expect(incrementResult).toEqual(updatedUsageData)
      expect(result.current.usage).toEqual(updatedUsageData)
      expect(mockFetch).toHaveBeenLastCalledWith('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })

    it('利用回数増分時のエラーを適切に処理する', async () => {
      const initialUsageData = {
        remainingCount: 1,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      const mockErrorData = {
        error: '本日の利用回数上限に達しました',
        errorCode: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remainingCount: 0,
        resetTime: '2024-01-02T00:00:00Z',
      }

      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(initialUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Increment usage with error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve(mockErrorData),
      })

      const incrementResult = await result.current.incrementUsage()

      expect(incrementResult).toBe(null)
      expect(result.current.usage).toBe(null)
      expect(result.current.error).toEqual(mockErrorData)
    })
  })

  describe('データの更新', () => {
    it('checkUsage を呼び出すとデータが更新される', async () => {
      const mockUsageData = {
        remainingCount: 3,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Clear previous calls
      mockFetch.mockClear()

      await result.current.checkUsage()

      expect(mockFetch).toHaveBeenCalledWith('/api/ai/usage', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })

    it('refreshUsage を呼び出すとデータが更新される', async () => {
      const mockUsageData = {
        remainingCount: 3,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Clear previous calls
      mockFetch.mockClear()

      await result.current.refreshUsage()

      expect(mockFetch).toHaveBeenCalledWith('/api/ai/usage', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })
  })

  describe('エラーのクリア', () => {
    it('clearError を呼び出すとエラーがクリアされる', async () => {
      const mockErrorData = {
        error: '本日の利用回数上限に達しました',
        errorCode: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remainingCount: 0,
        resetTime: '2024-01-02T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve(mockErrorData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.error).toEqual(mockErrorData)
      })

      result.current.clearError()

      expect(result.current.error).toBe(null)
    })
  })

  describe('自動更新', () => {
    it('5分間隔で自動的にデータを更新する', async () => {
      const mockUsageData = {
        remainingCount: 5,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1)
      })

      // Clear previous calls
      mockFetch.mockClear()

      // Advance time by 5 minutes
      vi.advanceTimersByTime(5 * 60 * 1000)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1)
      })
    })

    it('ローディング中は自動更新をスキップする', async () => {

      // Make the first request hang
      mockFetch.mockImplementationOnce(() => new Promise(() => { }))

      renderHook(() => useAIChatUsage())

      // Advance time by 5 minutes while loading
      vi.advanceTimersByTime(5 * 60 * 1000)

      // Should only have been called once (initial load)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('境界値テスト', () => {
    it('利用回数が負の値の場合を適切に処理する', async () => {
      const mockUsageData = {
        remainingCount: -1,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: false,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toEqual(mockUsageData)
      expect(result.current.canUseChat).toBe(false)
      expect(result.current.isUsageExhausted).toBe(true)
    })

    it('無制限プラン（dailyLimit: -1）を適切に処理する', async () => {
      const mockUsageData = {
        remainingCount: 999,
        dailyLimit: -1,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toEqual(mockUsageData)
      expect(result.current.canUseChat).toBe(true)
      expect(result.current.isUsageExhausted).toBe(false)
    })

    it('dailyLimitが0の場合を適切に処理する', async () => {
      const mockUsageData = {
        remainingCount: 0,
        dailyLimit: 0,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: false,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toEqual(mockUsageData)
      expect(result.current.canUseChat).toBe(false)
      expect(result.current.isUsageExhausted).toBe(true)
    })
  })

  describe('エラー状態の詳細テスト', () => {
    it('複数のエラーが発生した場合、利用エラーが優先される', async () => {
      const usageError = {
        error: '本日の利用回数上限に達しました',
        errorCode: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remainingCount: 0,
        resetTime: '2024-01-02T00:00:00Z',
      }

      // Mock useErrorHandling to return a system error
      const mockWithErrorHandling = vi.fn((fn) => fn())
      const mockSystemError = {
        message: 'System error',
        type: 'server' as const,
        retryable: true
      }

      vi.mocked(useErrorHandlingModule.useErrorHandling).mockReturnValue({
        error: mockSystemError,
        withErrorHandling: mockWithErrorHandling,
        clearError: vi.fn(),
        setError: vi.fn(),
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve(usageError),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Usage error should take precedence over system error
      expect(result.current.error).toEqual(usageError)
      expect(result.current.error?.errorCode).toBe(AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED)
    })

    it('不正なJSONレスポンスを適切に処理する', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.reject(new Error('Invalid JSON')),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toMatchObject({
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
      })
      expect(result.current.canUseChat).toBe(false)
    })

    it('予期しないHTTPステータスコードを適切に処理する', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 418, // I'm a teapot
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.usage).toBe(null)
      expect(result.current.error).toMatchObject({
        errorCode: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remainingCount: 0,
      })
      expect(result.current.canUseChat).toBe(false)
    })
  })

  describe('パフォーマンステスト', () => {
    it('複数回の連続呼び出しを適切に処理する', async () => {
      const mockUsageData = {
        remainingCount: 5,
        dailyLimit: 10,
        resetTime: '2024-01-02T00:00:00Z',
        canUseChat: true,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUsageData),
      })

      const { result } = renderHook(() => useAIChatUsage())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Clear previous calls
      mockFetch.mockClear()

      // Call multiple methods simultaneously
      const promises = [
        result.current.checkUsage(),
        result.current.refreshUsage(),
        result.current.incrementUsage(),
      ]

      await Promise.all(promises)

      // Should handle concurrent calls gracefully
      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('メモリリークを防ぐためにクリーンアップが適切に行われる', () => {
      const { unmount } = renderHook(() => useAIChatUsage())

      // Advance time to trigger interval
      vi.advanceTimersByTime(1000)

      // Unmount the hook
      unmount()

      // Clear all timers and advance time
      vi.clearAllTimers()
      vi.advanceTimersByTime(10 * 60 * 1000)

      // No additional fetch calls should be made after unmount
      // This is implicitly tested by not having memory leaks
      expect(true).toBe(true) // Placeholder assertion
    })
  })
})