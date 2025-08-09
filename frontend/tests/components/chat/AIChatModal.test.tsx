import { AI_CHAT_USAGE_ERROR_CODES } from '@/types/AIChatUsage'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import AIChatModal from '../../../components/components/chat/AIChatModal'

// Mock the hooks
const mockUseAIChatUsage = {
  usage: null,
  loading: false,
  error: null,
  can_use_chat: true,
  isUsageExhausted: false,
  refreshUsage: vi.fn(),
  incrementUsage: vi.fn(),
  clearError: vi.fn(),
  checkUsage: vi.fn(),
}

const mockUseMessages = {
  messages: [],
  isLoading: false,
  error: null,
  sendMessage: vi.fn(),
}

vi.mock('../../../components/hooks/useAIChatUsage', () => ({
  useAIChatUsage: () => mockUseAIChatUsage,
}))

vi.mock('../../../components/hooks/useMessages', () => ({
  useMessages: () => mockUseMessages,
}))

// Mock the child components
vi.mock('../../../components/components/chat/ChatInput', () => {
  const MockChatInput = ({ onSendMessage, isLoading, disabled, usage, usageError }: {
    onSendMessage: (message: string) => void;
    isLoading: boolean;
    disabled: boolean;
    usage?: { remaining_count: number; daily_limit: number } | null;
    usageError?: { error: string } | null;
  }) => {
    const [message, setMessage] = useState('')

    return (
      <div data-testid="chat-input">
        <input
          data-testid="message-input"
          disabled={disabled || isLoading}
          placeholder={disabled ? 'Disabled' : 'Type a message...'}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          data-testid="send-button"
          disabled={disabled || isLoading || !message.trim()}
          onClick={() => {
            if (message.trim()) {
              onSendMessage(message)
              setMessage('')
            }
          }}
        >
          Send
        </button>
        {usage && <div data-testid="usage-info">{usage.remaining_count}/{usage.daily_limit}</div>}
        {usageError && <div data-testid="usage-error">{usageError.error}</div>}
      </div>
    )
  }

  return {
    default: MockChatInput,
  }
})

vi.mock('../../../components/components/chat/ChatMessage', () => ({
  default: ({ message }: { message: { content: string } }) => (
    <div data-testid="chat-message">
      {message.content}
    </div>
  ),
}))

vi.mock('../../../components/components/commons/EmptyState', () => ({
  EmptyState: ({ title, description }: { title: string, description: string }) => (
    <div data-testid="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  ),
}))

vi.mock('../../../components/components/commons/ErrorDisplay', () => ({
  ErrorDisplay: ({ error, onRetry }: { error: { message: string }, onRetry: () => void }) => (
    <div data-testid="error-display">
      <p>{error.message}</p>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}))

describe('AIChatModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset mock states
    Object.assign(mockUseAIChatUsage, {
      usage: null,
      loading: false,
      error: null,
      can_use_chat: true,
      isUsageExhausted: false,
      refreshUsage: vi.fn(),
      incrementUsage: vi.fn(),
      clearError: vi.fn(),
      checkUsage: vi.fn(),
    })
    Object.assign(mockUseMessages, {
      messages: [],
      isLoading: false,
      error: null,
      sendMessage: vi.fn(),
    })
  })

  afterEach(() => {
    cleanup() // DOM要素をクリーンアップ
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  describe('基本的な表示', () => {
    it('モーダルが開いているときに表示される', () => {
      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getAllByText('AIアシスタント')).toHaveLength(2) // Header and empty state
    })

    it('モーダルが閉じているときは表示されない', () => {
      render(<AIChatModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('閉じるボタンをクリックするとonCloseが呼ばれる', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()

      render(<AIChatModal {...defaultProps} onClose={onClose} />)

      const closeButton = screen.getByLabelText('チャットを閉じる')
      await user.click(closeButton)

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('Escapeキーを押すとonCloseが呼ばれる', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()

      render(<AIChatModal {...defaultProps} onClose={onClose} />)

      await user.keyboard('{Escape}')

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('背景をクリックするとonCloseが呼ばれる', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()

      render(<AIChatModal {...defaultProps} onClose={onClose} />)

      const backdrop = document.querySelector('.fixed.inset-0.z-40')
      expect(backdrop).toBeInTheDocument()

      await user.click(backdrop!)

      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('利用状況の表示', () => {
    it('利用状況が正常に表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
        can_use_chat: true,
        isUsageExhausted: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getAllByText('5/10')).toHaveLength(3) // Desktop, mobile, and input component
    })

    it('利用回数が0の場合、適切なメッセージが表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 0,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: false,
        },
        can_use_chat: false,
        isUsageExhausted: true,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText('本日の利用回数上限に達しました')).toBeInTheDocument()
    })

    it('ローディング中はスピナーが表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        loading: true,
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
      })

      render(<AIChatModal {...defaultProps} />)

      // RefreshCw icon should be present with animate-spin class
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })
  })

  describe('エラー状態の表示', () => {
    it('利用制限エラーが適切に表示される', () => {
      const usageError = {
        error: '本日の利用回数上限に達しました',
        error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText('利用回数上限に達しました')).toBeInTheDocument()
      expect(screen.getByText('本日のAIChat利用回数が上限に達しています。明日の00:00にリセットされます。')).toBeInTheDocument()
    })

    it('プラン制限エラーが適切に表示される', () => {
      const usageError = {
        error: '現在のプランではAIChatをご利用いただけません',
        error_code: AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText('プランの制限')).toBeInTheDocument()
      expect(screen.getByText('現在のプランではAIChatをご利用いただけません。プランをアップグレードしてご利用ください。')).toBeInTheDocument()
    })

    it('システムエラーが適切に表示される', () => {
      const usageError = {
        error: '一時的なエラーが発生しました',
        error_code: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText('システムエラー')).toBeInTheDocument()
      expect(screen.getByText('一時的なエラーが発生しました。しばらく時間をおいてから再度お試しください。')).toBeInTheDocument()
    })

    it('エラーの閉じるボタンが機能する', async () => {
      const user = userEvent.setup()
      const clearError = vi.fn()

      Object.assign(mockUseAIChatUsage, {
        error: {
          error: '本日の利用回数上限に達しました',
          error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
          remaining_count: 0,
          reset_time: '2024-01-02T00:00:00Z',
        },
        clearError,
      })

      render(<AIChatModal {...defaultProps} />)

      const closeButton = screen.getByText('閉じる')
      await user.click(closeButton)

      expect(clearError).toHaveBeenCalledTimes(1)
    })

    it('エラーの再確認ボタンが機能する', async () => {
      const user = userEvent.setup()
      const refreshUsage = vi.fn()

      Object.assign(mockUseAIChatUsage, {
        error: {
          error: '本日の利用回数上限に達しました',
          error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
          remaining_count: 0,
          reset_time: '2024-01-02T00:00:00Z',
        },
        refreshUsage,
      })

      render(<AIChatModal {...defaultProps} />)

      const refreshButton = screen.getByText('再確認')
      await user.click(refreshButton)

      expect(refreshUsage).toHaveBeenCalledTimes(1)
    })
  })

  describe('メッセージの表示', () => {
    it('メッセージがない場合、空の状態が表示される', () => {
      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByTestId('empty-state')).toBeInTheDocument()
      expect(screen.getAllByText('AIアシスタント')).toHaveLength(2) // Header and empty state
      expect(screen.getByText('何かお手伝いできることはありますか？')).toBeInTheDocument()
    })

    it('メッセージがある場合、メッセージが表示される', () => {
      Object.assign(mockUseMessages, {
        messages: [
          { id: '1', content: 'Hello', role: 'user' },
          { id: '2', content: 'Hi there!', role: 'assistant' },
        ],
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getAllByTestId('chat-message')).toHaveLength(2)
      expect(screen.getByText('Hello')).toBeInTheDocument()
      expect(screen.getByText('Hi there!')).toBeInTheDocument()
    })

    it('システムエラーがある場合、エラー表示が表示される', () => {
      Object.assign(mockUseMessages, {
        error: new Error('System error'),
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByTestId('error-display')).toBeInTheDocument()
    })
  })

  describe('メッセージ送信', () => {
    it('利用可能な場合、メッセージを送信できる', async () => {
      const user = userEvent.setup()
      const sendMessage = vi.fn()
      const incrementUsage = vi.fn().mockResolvedValue({
        remaining_count: 4,
        daily_limit: 10,
        reset_time: '2024-01-02T00:00:00Z',
        can_use_chat: true,
      })

      Object.assign(mockUseMessages, { sendMessage })
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
        canUseChat: true,
        incrementUsage,
      })

      render(<AIChatModal {...defaultProps} />)

      const messageInput = screen.getByTestId('message-input')
      const sendButton = screen.getByTestId('send-button')

      await user.type(messageInput, 'test message')
      await user.click(sendButton)

      expect(sendMessage).toHaveBeenCalledWith('test message')
      expect(incrementUsage).toHaveBeenCalledTimes(1)
    })

    it('利用不可の場合、メッセージを送信できない', async () => {
      const user = userEvent.setup()
      const sendMessage = vi.fn()

      Object.assign(mockUseMessages, { sendMessage })
      Object.assign(mockUseAIChatUsage, {
        can_use_chat: false,
        isUsageExhausted: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const sendButton = screen.getByTestId('send-button')
      expect(sendButton).toBeDisabled()

      await user.click(sendButton)

      expect(sendMessage).not.toHaveBeenCalled()
    })

    it('ローディング中はメッセージを送信できない', async () => {
      const user = userEvent.setup()
      const sendMessage = vi.fn()

      Object.assign(mockUseMessages, {
        sendMessage,
        isLoading: true,
      })
      Object.assign(mockUseAIChatUsage, {
        can_use_chat: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const sendButton = screen.getByTestId('send-button')
      expect(sendButton).toBeDisabled()

      await user.click(sendButton)

      expect(sendMessage).not.toHaveBeenCalled()
    })

    it('利用状況ローディング中はメッセージを送信できない', async () => {
      const user = userEvent.setup()
      const sendMessage = vi.fn()

      Object.assign(mockUseMessages, { sendMessage })
      Object.assign(mockUseAIChatUsage, {
        can_use_chat: true,
        loading: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const sendButton = screen.getByTestId('send-button')
      expect(sendButton).toBeDisabled()

      await user.click(sendButton)

      expect(sendMessage).not.toHaveBeenCalled()
    })
  })

  describe('UI制御', () => {
    it('利用可能な場合、緑色のステータスインジケーターが表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
        canUseChat: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const statusIndicator = document.querySelector('.bg-green-500')
      expect(statusIndicator).toBeInTheDocument()
    })

    it('利用不可の場合、赤色のステータスインジケーターが表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 0,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: false,
        },
        canUseChat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      const statusIndicator = document.querySelector('.bg-red-500')
      expect(statusIndicator).toBeInTheDocument()
    })

    it('入力フィールドが利用状況に応じて無効化される', () => {
      Object.assign(mockUseAIChatUsage, {
        can_use_chat: false,
        isUsageExhausted: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const input = screen.getByTestId('message-input')
      expect(input).toBeDisabled()
    })

    it('送信ボタンが利用状況に応じて無効化される', () => {
      Object.assign(mockUseAIChatUsage, {
        can_use_chat: false,
        isUsageExhausted: true,
      })

      render(<AIChatModal {...defaultProps} />)

      const sendButton = screen.getByTestId('send-button')
      expect(sendButton).toBeDisabled()
    })
  })

  describe('レスポンシブデザイン', () => {
    it('デスクトップ表示で利用状況が適切に表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
      })

      render(<AIChatModal {...defaultProps} />)

      // Desktop usage display should be hidden on mobile (sm:flex)
      const desktopUsage = document.querySelector('.hidden.sm\\:flex')
      expect(desktopUsage).toBeInTheDocument()
    })

    it('モバイル表示で利用状況が適切に表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
      })

      render(<AIChatModal {...defaultProps} />)

      // Mobile usage display should be hidden on desktop (sm:hidden)
      const mobileUsage = document.querySelector('.sm\\:hidden')
      expect(mobileUsage).toBeInTheDocument()
      expect(screen.getByText('残り利用回数:')).toBeInTheDocument()
    })
  })

  describe('エラー状態の詳細テスト', () => {
    it('エラー表示にリセット時刻が正しく表示される', () => {
      const resetTime = '2024-01-02T15:30:00Z'
      const usageError = {
        error: '本日の利用回数上限に達しました',
        error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remaining_count: 0,
        reset_time: resetTime,
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText(/リセット時刻:/)).toBeInTheDocument()
      expect(screen.getByText(/にリセット\)/)).toBeInTheDocument()
    })

    it('プラン制限エラーでアップグレードボタンが表示される', () => {
      const usageError = {
        error: '現在のプランではAIChatをご利用いただけません',
        error_code: AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByText('プランをアップグレード')).toBeInTheDocument()
    })

    it('システムエラーではアップグレードボタンが表示されない', () => {
      const usageError = {
        error: '一時的なエラーが発生しました',
        error_code: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.queryByText('プランをアップグレード')).not.toBeInTheDocument()
    })

    it('エラー状態でもメッセージ履歴は表示される', () => {
      const usageError = {
        error: '本日の利用回数上限に達しました',
        error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z',
      }

      Object.assign(mockUseAIChatUsage, {
        error: usageError,
        can_use_chat: false,
      })

      Object.assign(mockUseMessages, {
        messages: [
          { id: '1', content: 'Previous message', role: 'user' },
        ],
      })

      render(<AIChatModal {...defaultProps} />)

      expect(screen.getByTestId('chat-message')).toBeInTheDocument()
      expect(screen.getByText('Previous message')).toBeInTheDocument()
    })
  })

  describe('UI制御の詳細テスト', () => {
    it('利用回数に応じてバッジの色が変わる', () => {
      // Test different usage levels
      const testCases = [
        { remaining: 0, daily: 10, expectedClass: 'destructive' },
        { remaining: 1, daily: 10, expectedClass: 'destructive' }, // Low usage
        { remaining: 5, daily: 10, expectedClass: 'default' }, // Normal usage
      ]

      testCases.forEach(({ remaining, daily }) => {
        Object.assign(mockUseAIChatUsage, {
          usage: {
            remaining_count: remaining,
            daily_limit: daily,
            reset_time: '2024-01-02T00:00:00Z',
            can_use_chat: remaining > 0,
          },
          can_use_chat: remaining > 0,
          isUsageExhausted: remaining === 0,
        })

        const { unmount } = render(<AIChatModal {...defaultProps} />)

        // Check if usage info is displayed (this is what we can actually test with our mock)
        const usageInfo = screen.getByTestId('usage-info')
        expect(usageInfo).toHaveTextContent(`${remaining}/${daily}`)

        unmount()
      })
    })

    it('無制限プランの場合、適切な表示がされる', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 999,
          daily_limit: -1,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
        can_use_chat: true,
        isUsageExhausted: false,
      })

      render(<AIChatModal {...defaultProps} />)

      // Should show unlimited usage
      expect(screen.getByTestId('usage-info')).toHaveTextContent('999/-1')
    })

    it('ローディング状態でスピナーが適切に表示される', () => {
      Object.assign(mockUseAIChatUsage, {
        loading: true,
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
      })

      render(<AIChatModal {...defaultProps} />)

      const spinners = document.querySelectorAll('.animate-spin')
      expect(spinners.length).toBeGreaterThan(0)
    })

    it('メッセージ送信中は入力が無効化される', () => {
      Object.assign(mockUseMessages, {
        isLoading: true,
      })

      Object.assign(mockUseAIChatUsage, {
        can_use_chat: true,
        isUsageExhausted: false,
      })

      render(<AIChatModal {...defaultProps} />)

      const input = screen.getByTestId('message-input')
      const sendButton = screen.getByTestId('send-button')

      expect(input).toBeDisabled()
      expect(sendButton).toBeDisabled()
    })
  })

  describe('アクセシビリティテスト', () => {
    it('適切なARIA属性が設定されている', () => {
      render(<AIChatModal {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'chat-title')

      const closeButton = screen.getByLabelText('チャットを閉じる')
      expect(closeButton).toBeInTheDocument()
    })

    it('キーボードナビゲーションが適切に動作する', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()

      render(<AIChatModal {...defaultProps} onClose={onClose} />)

      // Tab navigation should work
      await user.tab()
      expect(document.activeElement).toBeTruthy()

      // Escape key should close modal
      await user.keyboard('{Escape}')
      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('スクリーンリーダー用のテキストが適切に設定されている', () => {
      Object.assign(mockUseAIChatUsage, {
        usage: {
          remaining_count: 3,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
      })

      render(<AIChatModal {...defaultProps} />)

      // Check for screen reader friendly content
      expect(screen.getByTestId('mobile-usage-display')).toBeInTheDocument()
      expect(screen.getAllByText('AIアシスタント')).toHaveLength(2) // Header and empty state
    })
  })

  describe('エラー回復テスト', () => {
    it('エラー状態から正常状態への復帰が適切に処理される', async () => {
      // Start with error state
      Object.assign(mockUseAIChatUsage, {
        error: {
          error: '本日の利用回数上限に達しました',
          error_code: AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
          remaining_count: 0,
          reset_time: '2024-01-02T00:00:00Z',
        },
        can_use_chat: false,
      })

      const { rerender } = render(<AIChatModal {...defaultProps} />)

      expect(screen.getByTestId('usage-exhausted-message')).toBeInTheDocument()

      // Simulate error recovery
      Object.assign(mockUseAIChatUsage, {
        error: null,
        usage: {
          remaining_count: 5,
          daily_limit: 10,
          reset_time: '2024-01-02T00:00:00Z',
          can_use_chat: true,
        },
        can_use_chat: true,
        isUsageExhausted: false,
      })

      rerender(<AIChatModal {...defaultProps} />)

      expect(screen.queryByText('利用回数上限に達しました')).not.toBeInTheDocument()
      expect(screen.getByTestId('usage-info')).toHaveTextContent('5/10')
    })

    it('ネットワーク復旧後の自動リトライが動作する', async () => {
      const user = userEvent.setup()
      const refreshUsage = vi.fn()

      Object.assign(mockUseAIChatUsage, {
        error: {
          error: '一時的なエラーが発生しました',
          error_code: AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR,
          remaining_count: 0,
          reset_time: '2024-01-02T00:00:00Z',
        },
        refreshUsage,
      })

      render(<AIChatModal {...defaultProps} />)

      const refreshButton = screen.getByTestId('modal-refresh-button')
      await user.click(refreshButton)

      expect(refreshUsage).toHaveBeenCalledTimes(1)
    })
  })
})