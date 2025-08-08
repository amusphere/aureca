/**
 * Integration tests for frontend-backend AI Chat usage API communication
 */

import { AIChatUsage, AIChatUsageError } from '@/types/AIChatUsage'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('AI Chat Usage API Communication Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('GET /api/ai/usage endpoint', () => {
    it('should successfully fetch usage data', async () => {
      const mockUsageData: AIChatUsage = {
        remaining_count: 7,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUsageData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(true)
      expect(response.status).toBe(200)
      expect(data).toEqual(mockUsageData)
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/usage')
    })

    it('should handle usage limit exceeded error (429)', async () => {
      const mockErrorData: AIChatUsageError = {
        error: '本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(429)
      expect(data).toEqual(mockErrorData)
      expect(data.error_code).toBe('USAGE_LIMIT_EXCEEDED')
    })

    it('should handle plan restriction error (403)', async () => {
      const mockErrorData: AIChatUsageError = {
        error: 'freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。',
        error_code: 'PLAN_RESTRICTION',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(403)
      expect(data).toEqual(mockErrorData)
      expect(data.error_code).toBe('PLAN_RESTRICTION')
    })

    it('should handle system error (500)', async () => {
      const mockErrorData: AIChatUsageError = {
        error: '一時的なエラーが発生しました。しばらく後にお試しください。',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
      expect(data).toEqual(mockErrorData)
      expect(data.error_code).toBe('SYSTEM_ERROR')
    })

    it('should handle network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetch('/api/ai/usage')).rejects.toThrow('Network error')
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/usage')
    })
  })

  describe('POST /api/ai/usage/increment endpoint', () => {
    it('should successfully increment usage', async () => {
      const mockUpdatedUsage: AIChatUsage = {
        remaining_count: 6,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUpdatedUsage
      })

      const response = await fetch('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()

      expect(response.ok).toBe(true)
      expect(response.status).toBe(200)
      expect(data).toEqual(mockUpdatedUsage)
      expect(data.remaining_count).toBe(6)
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
    })

    it('should handle increment when at limit (429)', async () => {
      const mockErrorData: AIChatUsageError = {
        error: '本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(429)
      expect(data).toEqual(mockErrorData)
      expect(data.error_code).toBe('USAGE_LIMIT_EXCEEDED')
    })

    it('should handle plan restriction on increment (403)', async () => {
      const mockErrorData: AIChatUsageError = {
        error: 'freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。',
        error_code: 'PLAN_RESTRICTION',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage/increment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(403)
      expect(data).toEqual(mockErrorData)
      expect(data.error_code).toBe('PLAN_RESTRICTION')
    })
  })

  describe('Response format validation', () => {
    it('should validate successful response format', async () => {
      const mockUsageData: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUsageData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      // Validate all required fields are present
      expect(data).toHaveProperty('remaining_count')
      expect(data).toHaveProperty('daily_limit')
      expect(data).toHaveProperty('reset_time')
      expect(data).toHaveProperty('can_use_chat')

      // Validate field types
      expect(typeof data.remaining_count).toBe('number')
      expect(typeof data.daily_limit).toBe('number')
      expect(typeof data.reset_time).toBe('string')
      expect(typeof data.can_use_chat).toBe('boolean')

      // Validate field values
      expect(data.remaining_count).toBeGreaterThanOrEqual(0)
      expect(data.daily_limit).toBeGreaterThan(0)
      expect(new Date(data.reset_time)).toBeInstanceOf(Date)
    })

    it('should validate error response format', async () => {
      const mockErrorData: AIChatUsageError = {
        error: 'Test error message',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      // Validate all required error fields are present
      expect(data).toHaveProperty('error')
      expect(data).toHaveProperty('error_code')
      expect(data).toHaveProperty('remaining_count')
      expect(data).toHaveProperty('reset_time')

      // Validate field types
      expect(typeof data.error).toBe('string')
      expect(typeof data.error_code).toBe('string')
      expect(typeof data.remaining_count).toBe('number')
      expect(typeof data.reset_time).toBe('string')

      // Validate field values
      expect(data.error.length).toBeGreaterThan(0)
      expect(['USAGE_LIMIT_EXCEEDED', 'PLAN_RESTRICTION', 'SYSTEM_ERROR']).toContain(data.error_code)
      expect(data.remaining_count).toBeGreaterThanOrEqual(0)
      expect(new Date(data.resetTime)).toBeInstanceOf(Date)
    })
  })

  describe('Error handling consistency', () => {
    it('should handle malformed JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        }
      })

      const response = await fetch('/api/ai/usage')

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)

      // Should throw when trying to parse invalid JSON
      await expect(response.json()).rejects.toThrow('Invalid JSON')
    })

    it('should handle empty response bodies', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => null
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
      expect(data).toBeNull()
    })

    it('should handle unexpected status codes', async () => {
      const mockErrorData: AIChatUsageError = {
        error: 'Unexpected error',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 418, // I'm a teapot - unexpected status
        json: async () => mockErrorData
      })

      const response = await fetch('/api/ai/usage')
      const data = await response.json()

      expect(response.ok).toBe(false)
      expect(response.status).toBe(418)
      expect(data).toEqual(mockErrorData)
    })
  })

  describe('Request/Response timing', () => {
    it('should handle slow responses', async () => {
      const mockUsageData: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      // Simulate slow response
      mockFetch.mockImplementationOnce(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: async () => mockUsageData
          }), 100)
        )
      )

      const startTime = Date.now()
      const response = await fetch('/api/ai/usage')
      const endTime = Date.now()
      const data = await response.json()

      expect(endTime - startTime).toBeGreaterThanOrEqual(100)
      expect(response.ok).toBe(true)
      expect(data).toEqual(mockUsageData)
    })

    it('should handle request timeouts', async () => {
      // Simulate timeout
      mockFetch.mockImplementationOnce(() =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Request timeout')), 50)
        )
      )

      await expect(fetch('/api/ai/usage')).rejects.toThrow('Request timeout')
    })
  })

  describe('Concurrent requests handling', () => {
    it('should handle multiple concurrent GET requests', async () => {
      const mockUsageData: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockUsageData
      })

      // Make multiple concurrent requests
      const requests = Array(5).fill(null).map(() => fetch('/api/ai/usage'))
      const responses = await Promise.all(requests)

      // All should succeed
      responses.forEach(response => {
        expect(response.ok).toBe(true)
        expect(response.status).toBe(200)
      })

      expect(mockFetch).toHaveBeenCalledTimes(5)
    })

    it('should handle concurrent increment requests', async () => {
      const mockUpdatedUsage: AIChatUsage = {
        remaining_count: 4,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockUpdatedUsage
      })

      // Make multiple concurrent increment requests
      const requests = Array(3).fill(null).map(() =>
        fetch('/api/ai/usage/increment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      )
      const responses = await Promise.all(requests)

      // All should succeed (backend handles concurrency)
      responses.forEach(response => {
        expect(response.ok).toBe(true)
        expect(response.status).toBe(200)
      })

      expect(mockFetch).toHaveBeenCalledTimes(3)
    })
  })
})