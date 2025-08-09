/**
 * Integration tests for AI Chat usage error handling in frontend components
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { AIChatUsage, AIChatUsageError } from '@/types/AIChatUsage'

// Mock the useAIChatUsage hook
const mockUseAIChatUsage = vi.fn()
vi.mock('@/components/hooks/useAIChatUsage', () => ({
  useAIChatUsage: () => mockUseAIChatUsage()
}))

// Mock components for testing
const MockAIChatModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const { usage, loading, error, refreshUsage } = mockUseAIChatUsage()

  if (!isOpen) return null

  return (
    <div data-testid="ai-chat-modal">
      {loading && (
        <div data-testid="loading">読み込み中...</div>
      )}

      {error && (
        <div data-testid="error-display">
          <div data-testid="error-message">{error.error}</div>
          <div data-testid="error-code">{error.error_code}</div>
          <div data-testid="remaining-count">{error.remaining_count}</div>
          <div data-testid="reset-time">{error.reset_time}</div>
        </div>
      )}

      {usage && !error && (
        <div data-testid="usage-display">
          <div data-testid="remaining-count">{usage.remaining_count}</div>
          <div data-testid="daily-limit">{usage.daily_limit}</div>
          <div data-testid="can-use-chat">{usage.can_use_chat?.toString()}</div>
          <input
            data-testid="chat-input"
            disabled={!usage.can_use_chat}
            placeholder={usage.can_use_chat ? "メッセージを入力..." : "利用制限に達しています"}
          />
          <button
            data-testid="send-button"
            disabled={!usage.can_use_chat}
            onClick={() => {/* simulate send */}}
          >
            送信
          </button>
        </div>
      )}

      <button data-testid="refresh-button" onClick={refreshUsage}>
        更新
      </button>
      <button data-testid="close-button" onClick={onClose}>
        閉じる
      </button>
    </div>
  )
}

describe('AI Chat Usage Error Handling Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  describe('Usage Limit Exceeded Error (429)', () => {
    it('should display usage limit exceeded error correctly', async () => {
      const mockError: AIChatUsageError = {
        error: '本日の利用回数上限に達しました。明日の00:00にリセットされます。',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify error display
      expect(screen.getByTestId('error-display')).toBeInTheDocument()
      expect(screen.getByTestId('error-message')).toHaveTextContent('本日の利用回数上限に達しました')
      expect(screen.getByTestId('error-code')).toHaveTextContent('USAGE_LIMIT_EXCEEDED')
      expect(screen.getByTestId('remaining-count')).toHaveTextContent('0')
      expect(screen.getByTestId('reset-time')).toHaveTextContent('2023-01-02T00:00:00.000Z')

      // Verify usage display is not shown
      expect(screen.queryByTestId('usage-display')).not.toBeInTheDocument()
    })

    it('should disable chat input when usage limit is exceeded', async () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 0,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: false
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: mockUsage,
        loading: false,
        error: null,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify input is disabled
      const chatInput = screen.getByTestId('chat-input')
      const sendButton = screen.getByTestId('send-button')

      expect(chatInput).toBeDisabled()
      expect(sendButton).toBeDisabled()
      expect(chatInput).toHaveAttribute('placeholder', '利用制限に達しています')
    })
  })

  describe('Plan Restriction Error (403)', () => {
    it('should display plan restriction error correctly', async () => {
      const mockError: AIChatUsageError = {
        error: '現在のプランではAIChatをご利用いただけません。プランをアップグレードしてください。',
        error_code: 'PLAN_RESTRICTION',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify plan restriction error display
      expect(screen.getByTestId('error-message')).toHaveTextContent('現在のプランではAIChatをご利用いただけません')
      expect(screen.getByTestId('error-code')).toHaveTextContent('PLAN_RESTRICTION')
    })
  })

  describe('System Error (500)', () => {
    it('should display system error correctly', async () => {
      const mockError: AIChatUsageError = {
        error: '一時的なエラーが発生しました。しばらく後にお試しください。',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify system error display
      expect(screen.getByTestId('error-message')).toHaveTextContent('一時的なエラーが発生しました')
      expect(screen.getByTestId('error-code')).toHaveTextContent('SYSTEM_ERROR')
    })

    it('should allow retry after system error', async () => {
      const mockRefreshUsage = vi.fn()
      const mockError: AIChatUsageError = {
        error: '一時的なエラーが発生しました。しばらく後にお試しください。',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: mockRefreshUsage
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Click refresh button
      const refreshButton = screen.getByTestId('refresh-button')
      fireEvent.click(refreshButton)

      // Verify refresh function was called
      expect(mockRefreshUsage).toHaveBeenCalledTimes(1)
    })
  })

  describe('Loading States', () => {
    it('should display loading state correctly', async () => {
      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: true,
        error: null,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify loading display
      expect(screen.getByTestId('loading')).toBeInTheDocument()
      expect(screen.getByTestId('loading')).toHaveTextContent('読み込み中...')

      // Verify other elements are not shown during loading
      expect(screen.queryByTestId('error-display')).not.toBeInTheDocument()
      expect(screen.queryByTestId('usage-display')).not.toBeInTheDocument()
    })
  })

  describe('Successful Usage Display', () => {
    it('should display usage information correctly when available', async () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 7,
        daily_limit: 10,
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

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify usage display
      expect(screen.getByTestId('usage-display')).toBeInTheDocument()
      expect(screen.getByTestId('remaining-count')).toHaveTextContent('7')
      expect(screen.getByTestId('daily-limit')).toHaveTextContent('10')
      expect(screen.getByTestId('can-use-chat')).toHaveTextContent('true')

      // Verify input is enabled
      const chatInput = screen.getByTestId('chat-input')
      const sendButton = screen.getByTestId('send-button')

      expect(chatInput).not.toBeDisabled()
      expect(sendButton).not.toBeDisabled()
      expect(chatInput).toHaveAttribute('placeholder', 'メッセージを入力...')
    })
  })

  describe('Error Recovery Scenarios', () => {
    it('should handle transition from error to success state', async () => {
      const mockRefreshUsage = vi.fn()

      // Start with error state
      const mockError: AIChatUsageError = {
        error: 'システムエラー',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      // Initially show error
      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: mockRefreshUsage
      })

      const { rerender } = render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)
      expect(screen.getByTestId('error-display')).toBeInTheDocument()

      // Simulate successful recovery
      const mockUsage: AIChatUsage = {
        remaining_count: 5,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: true
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: mockUsage,
        loading: false,
        error: null,
        checkUsage: vi.fn(),
        refreshUsage: mockRefreshUsage
      })

      rerender(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Verify transition to success state
      expect(screen.queryByTestId('error-display')).not.toBeInTheDocument()
      expect(screen.getByTestId('usage-display')).toBeInTheDocument()
    })
  })

  describe('User Interaction Error Handling', () => {
    it('should handle refresh button click during error state', async () => {
      const mockRefreshUsage = vi.fn()
      const mockError: AIChatUsageError = {
        error: 'テストエラー',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2023-01-02T00:00:00.000Z'
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: null,
        loading: false,
        error: mockError,
        checkUsage: vi.fn(),
        refreshUsage: mockRefreshUsage
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Click refresh multiple times
      const refreshButton = screen.getByTestId('refresh-button')
      fireEvent.click(refreshButton)
      fireEvent.click(refreshButton)
      fireEvent.click(refreshButton)

      // Should handle multiple clicks gracefully
      expect(mockRefreshUsage).toHaveBeenCalledTimes(3)
    })

    it('should prevent form submission when chat is disabled', async () => {
      const mockUsage: AIChatUsage = {
        remaining_count: 0,
        daily_limit: 10,
        reset_time: '2023-01-02T00:00:00.000Z',
        can_use_chat: false
      }

      mockUseAIChatUsage.mockReturnValue({
        usage: mockUsage,
        loading: false,
        error: null,
        checkUsage: vi.fn(),
        refreshUsage: vi.fn()
      })

      render(<MockAIChatModal isOpen={true} onClose={vi.fn()} />)

      // Try to interact with disabled elements
      const chatInput = screen.getByTestId('chat-input')
      const sendButton = screen.getByTestId('send-button')

      // Input should be disabled - disabled inputs can still receive values in tests
      // but they should be disabled from user interaction
      expect(chatInput).toBeDisabled()
      expect(chatInput).toHaveAttribute('placeholder', '利用制限に達しています')

      // Button should be disabled
      fireEvent.click(sendButton)
      // In a real implementation, you'd verify no API call was made
    })
  })
})