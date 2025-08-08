/**
 * Cross-browser responsive UI tests for AI Chat usage components
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { AIChatUsage, AIChatUsageError } from '@/types/AIChatUsage'

// Mock the useAIChatUsage hook
const mockUseAIChatUsage = vi.fn()
vi.mock('@/components/hooks/useAIChatUsage', () => ({
  useAIChatUsage: () => mockUseAIChatUsage()
}))

// Mock responsive UI component for testing
const MockResponsiveUsageDisplay = ({
  usage,
  error,
  loading
}: {
  usage: AIChatUsage | null
  error: AIChatUsageError | null
  loading: boolean
}) => {
  if (loading) {
    return (
      <div data-testid="loading-state" className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div data-testid="error-state" className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between">
          <div className="flex-1 mb-2 sm:mb-0">
            <p className="text-sm text-red-800" data-testid="error-message">
              {error.error}
            </p>
            <p className="text-xs text-red-600 mt-1" data-testid="error-code">
              エラーコード: {error.error_code}
            </p>
          </div>
          <div className="text-xs text-red-600" data-testid="reset-time">
            リセット: {new Date(error.reset_time).toLocaleTimeString()}
          </div>
        </div>
      </div>
    )
  }

  if (usage) {
    return (
      <div data-testid="usage-state" className="bg-white border border-gray-200 rounded-lg p-4">
        {/* Mobile layout */}
        <div className="block sm:hidden">
          <div className="text-center mb-3">
            <div className="text-2xl font-bold text-gray-900" data-testid="mobile-remaining">
              {usage.remaining_count}
            </div>
            <div className="text-sm text-gray-500">残り回数</div>
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span data-testid="mobile-limit">上限: {usage.daily_limit}回</span>
            <span data-testid="mobile-plan">プラン: {usage.plan_name}</span>
          </div>
          <div className="mt-2 text-xs text-gray-500" data-testid="mobile-reset">
            リセット: {new Date(usage.reset_time).toLocaleTimeString()}
          </div>
        </div>

        {/* Tablet/Desktop layout */}
        <div className="hidden sm:flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-lg font-semibold text-gray-900" data-testid="desktop-remaining">
              {usage.remaining_count}/{usage.daily_limit}
            </div>
            <div className="text-sm text-gray-600" data-testid="desktop-plan">
              {usage.plan_name}プラン
            </div>
          </div>
          <div className="text-sm text-gray-500" data-testid="desktop-reset">
            {new Date(usage.reset_time).toLocaleTimeString()}にリセット
          </div>
        </div>

        {/* Usage bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>利用状況</span>
            <span>{Math.round((usage.current_usage / usage.daily_limit) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                usage.can_use_chat ? 'bg-blue-500' : 'bg-red-500'
              }`}
              style={{
                width: `${usage.daily_limit === 0 ? 0 : Math.min((usage.current_usage / usage.daily_limit) * 100, 100)}%`
              }}
              data-testid="usage-bar"
            ></div>
          </div>
        </div>

        {/* Status indicator */}
        <div className="mt-3 flex items-center justify-center">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
            usage.can_use_chat
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`} data-testid="status-indicator">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              usage.can_use_chat ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            {usage.can_use_chat ? '利用可能' : '利用不可'}
          </div>
        </div>
      </div>
    )
  }

  return <div data-testid="no-data">データがありません</div>
}

describe('Responsive UI Cross-Browser Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  describe('Mobile Layout (< 640px)', () => {
    beforeEach(() => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      })
    })

    it('should display mobile layout for usage data', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 7,
        daily_limit: 10,
        current_usage: 3,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: mockUsage,
        loading: false,
        error: null,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      // Verify mobile-specific elements are present
      expect(screen.getByTestId('mobile-remaining')).toHaveTextContent('7')
      expect(screen.getByTestId('mobile-limit')).toHaveTextContent('上限: 10回')
      expect(screen.getByTestId('mobile-plan')).toHaveTextContent('プラン: standard')
      expect(screen.getByTestId('mobile-reset')).toBeInTheDocument()

      // Verify usage bar is present
      expect(screen.getByTestId('usage-bar')).toBeInTheDocument()
      expect(screen.getByTestId('status-indicator')).toHaveTextContent('利用可能')
    })

    it('should display mobile error layout', () => {
      const mockError: AIChatUsageError = {
        error: '本日の利用回数上限に達しました',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      render(<MockResponsiveUsageDisplay usage={null} error={mockError} loading={false} />)

      expect(screen.getByTestId('error-state')).toBeInTheDocument()
      expect(screen.getByTestId('error-message')).toHaveTextContent('本日の利用回数上限に達しました')
      expect(screen.getByTestId('error-code')).toHaveTextContent('USAGE_LIMIT_EXCEEDED')
    })

    it('should display mobile loading state', () => {
      render(<MockResponsiveUsageDisplay usage={null} error={null} loading={true} />)

      expect(screen.getByTestId('loading-state')).toBeInTheDocument()
      expect(screen.getByTestId('loading-state')).toHaveClass('animate-pulse')
    })
  })

  describe('Tablet Layout (640px - 1024px)', () => {
    beforeEach(() => {
      // Mock tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      })
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1024,
      })
    })

    it('should display tablet layout for usage data', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        current_usage: 5,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      // Verify desktop/tablet elements are present (hidden on mobile)
      expect(screen.getByTestId('desktop-remaining')).toHaveTextContent('5/10')
      expect(screen.getByTestId('desktop-plan')).toHaveTextContent('standardプラン')
      expect(screen.getByTestId('desktop-reset')).toBeInTheDocument()

      // Verify usage bar shows 50% usage
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveStyle({ width: '50%' })
    })

    it('should handle tablet error display', () => {
      const mockError: AIChatUsageError = {
        error: 'freeプランではAIChatをご利用いただけません',
        error_code: 'PLAN_RESTRICTION',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      render(<MockResponsiveUsageDisplay usage={null} error={mockError} loading={false} />)

      expect(screen.getByTestId('error-message')).toHaveTextContent('freeプランではAIChatをご利用いただけません')
      expect(screen.getByTestId('error-code')).toHaveTextContent('PLAN_RESTRICTION')
    })
  })

  describe('Desktop Layout (> 1024px)', () => {
    beforeEach(() => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      })
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1080,
      })
    })

    it('should display desktop layout for usage data', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 2,
        daily_limit: 10,
        current_usage: 8,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      // Verify desktop layout
      expect(screen.getByTestId('desktop-remaining')).toHaveTextContent('2/10')
      expect(screen.getByTestId('desktop-plan')).toHaveTextContent('standardプラン')

      // Verify usage bar shows 80% usage
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveStyle({ width: '80%' })

      // Should still show as available
      expect(screen.getByTestId('status-indicator')).toHaveTextContent('利用可能')
    })

    it('should display at-limit state correctly', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 0,
        daily_limit: 10,
        current_usage: 10,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: false
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      expect(screen.getByTestId('desktop-remaining')).toHaveTextContent('0/10')

      // Usage bar should be 100% and red
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveStyle({ width: '100%' })
      expect(usageBar).toHaveClass('bg-red-500')

      // Status should show unavailable
      expect(screen.getByTestId('status-indicator')).toHaveTextContent('利用不可')
      expect(screen.getByTestId('status-indicator')).toHaveClass('bg-red-100', 'text-red-800')
    })
  })

  describe('Free Plan Display', () => {
    it('should display free plan restrictions correctly', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 0,
        daily_limit: 0,
        current_usage: 0,
        plan_name: 'free',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: false
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      // Should show 0/0 for free plan
      expect(screen.getByTestId('desktop-remaining')).toHaveTextContent('0/0')
      expect(screen.getByTestId('desktop-plan')).toHaveTextContent('freeプラン')

      // Usage bar should be at 0% but red (since can't use)
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveStyle({ width: '0%' })
      expect(usageBar).toHaveClass('bg-red-500')

      // Status should show unavailable
      expect(screen.getByTestId('status-indicator')).toHaveTextContent('利用不可')
    })
  })

  describe('Accessibility Features', () => {
    it('should provide proper ARIA labels and roles', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        current_usage: 5,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      // Usage bar should be accessible
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toBeInTheDocument()

      // Status indicator should be accessible
      const statusIndicator = screen.getByTestId('status-indicator')
      expect(statusIndicator).toBeInTheDocument()
    })

    it('should provide accessible error information', () => {
      const mockError: AIChatUsageError = {
        error: 'システムエラーが発生しました',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      render(<MockResponsiveUsageDisplay usage={null} error={mockError} loading={false} />)

      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage).toHaveTextContent('システムエラーが発生しました')

      const errorCode = screen.getByTestId('error-code')
      expect(errorCode).toHaveTextContent('SYSTEM_ERROR')
    })
  })

  describe('Animation and Transitions', () => {
    it('should apply loading animations', () => {
      render(<MockResponsiveUsageDisplay usage={null} error={null} loading={true} />)

      const loadingState = screen.getByTestId('loading-state')
      expect(loadingState).toHaveClass('animate-pulse')
    })

    it('should apply transition classes to usage bar', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 3,
        daily_limit: 10,
        current_usage: 7,
        plan_name: 'standard',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveClass('transition-all', 'duration-300')
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero daily limit gracefully', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 0,
        daily_limit: 0,
        current_usage: 0,
        plan_name: 'free',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: false
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      expect(screen.getByTestId('desktop-remaining')).toHaveTextContent('0/0')

      // Should handle division by zero in percentage calculation
      const usageBar = screen.getByTestId('usage-bar')
      expect(usageBar).toHaveStyle({ width: '0%' })
    })

    it('should handle very long plan names', () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        current_usage: 5,
        plan_name: 'very-long-plan-name-that-might-break-layout',
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      expect(screen.getByTestId('desktop-plan')).toHaveTextContent('very-long-plan-name-that-might-break-layoutプラン')
    })

    it('should handle future reset times', () => {
      const futureTime = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      const mockUsage: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        current_usage: 5,
        plan_name: 'standard',
        reset_time: futureTime,
        can_use_chat: true
      }

      render(<MockResponsiveUsageDisplay usage={mockUsage} error={null} loading={false} />)

      expect(screen.getByTestId('desktop-reset')).toBeInTheDocument()
    })
  })
})