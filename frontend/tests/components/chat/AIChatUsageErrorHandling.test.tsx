import { AI_CHAT_USAGE_ERROR_CODES, AIChatUsageUtils } from '@/types/AIChatUsage'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Test the error handling utilities and integration
describe('AIChatUsageErrorHandling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('AIChatUsageUtils', () => {
    describe('formatResetTime', () => {
      it('正常なISO文字列を日本語形式でフォーマットする', () => {
        const resetTime = '2024-01-02T00:00:00Z'
        const formatted = AIChatUsageUtils.formatResetTime(resetTime)

        expect(formatted).toMatch(/2024年/)
        expect(formatted).toMatch(/1月/)
        expect(formatted).toMatch(/2日/)
      })

      it('不正な日付文字列の場合、デフォルト値を返す', () => {
        const invalidTime = 'invalid-date'
        const formatted = AIChatUsageUtils.formatResetTime(invalidTime)

        expect(formatted).toBe('明日の00:00')
      })

      it('空文字列の場合、デフォルト値を返す', () => {
        const formatted = AIChatUsageUtils.formatResetTime('')

        expect(formatted).toBe('明日の00:00')
      })
    })

    describe('getTimeUntilReset', () => {
      beforeEach(() => {
        // Mock current time to 2024-01-01T12:00:00Z
        vi.useFakeTimers()
        vi.setSystemTime(new Date('2024-01-01T12:00:00Z'))
      })

      afterEach(() => {
        vi.useRealTimers()
      })

      it('12時間後のリセット時刻を正しく計算する', () => {
        const resetTime = '2024-01-02T00:00:00Z' // 12 hours later
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(resetTime)

        expect(timeUntil).toBe('約12時間後')
      })

      it('1時間30分後のリセット時刻を正しく計算する', () => {
        const resetTime = '2024-01-01T13:30:00Z' // 1.5 hours later
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(resetTime)

        expect(timeUntil).toBe('約1時間30分後')
      })

      it('30分後のリセット時刻を正しく計算する', () => {
        const resetTime = '2024-01-01T12:30:00Z' // 30 minutes later
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(resetTime)

        expect(timeUntil).toBe('約30分後')
      })

      it('1分以内のリセット時刻を正しく計算する', () => {
        const resetTime = '2024-01-01T12:00:30Z' // 30 seconds later
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(resetTime)

        expect(timeUntil).toBe('1分以内')
      })

      it('過去の時刻の場合、まもなくリセットを返す', () => {
        const resetTime = '2024-01-01T11:00:00Z' // 1 hour ago
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(resetTime)

        expect(timeUntil).toBe('まもなくリセット')
      })

      it('不正な日付の場合、デフォルト値を返す', () => {
        const invalidTime = 'invalid-date'
        const timeUntil = AIChatUsageUtils.getTimeUntilReset(invalidTime)

        expect(timeUntil).toBe('明日の00:00')
      })
    })

    describe('getErrorMessage', () => {
      it('シンプルなエラーメッセージを返す', () => {
        const message = AIChatUsageUtils.getErrorMessage(
          AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
          'simple'
        )

        expect(message).toBe('本日の利用回数上限に達しました')
      })

      it('詳細なエラーメッセージを返す', () => {
        const message = AIChatUsageUtils.getErrorMessage(
          AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED,
          'detailed'
        )

        expect(message).toBe('本日のAIChat利用回数が上限に達しています。明日の00:00にリセットされます。')
      })

      it('プレースホルダーメッセージを返す', () => {
        const message = AIChatUsageUtils.getErrorMessage(
          AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION,
          'placeholder'
        )

        expect(message).toBe('現在のプランではAIChatをご利用いただけません。プランをアップグレードしてください。')
      })

      it('デフォルトでシンプルメッセージを返す', () => {
        const message = AIChatUsageUtils.getErrorMessage(
          AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR
        )

        expect(message).toBe('一時的なエラーが発生しました')
      })
    })

    describe('getErrorTitle', () => {
      it('利用制限エラーのタイトルを返す', () => {
        const title = AIChatUsageUtils.getErrorTitle(
          AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED
        )

        expect(title).toBe('利用回数上限に達しました')
      })

      it('プラン制限エラーのタイトルを返す', () => {
        const title = AIChatUsageUtils.getErrorTitle(
          AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION
        )

        expect(title).toBe('プランの制限')
      })

      it('システムエラーのタイトルを返す', () => {
        const title = AIChatUsageUtils.getErrorTitle(
          AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR
        )

        expect(title).toBe('システムエラー')
      })
    })

    describe('getErrorActionText', () => {
      it('利用制限エラーのアクションテキストを返す', () => {
        const actionText = AIChatUsageUtils.getErrorActionText(
          AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED
        )

        expect(actionText).toBe('プランをアップグレード')
      })

      it('プラン制限エラーのアクションテキストを返す', () => {
        const actionText = AIChatUsageUtils.getErrorActionText(
          AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION
        )

        expect(actionText).toBe('プランをアップグレード')
      })

      it('システムエラーのアクションテキストを返す', () => {
        const actionText = AIChatUsageUtils.getErrorActionText(
          AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR
        )

        expect(actionText).toBe('再試行')
      })
    })

    describe('isRecoverableError', () => {
      it('利用制限エラーは回復可能と判定する', () => {
        const isRecoverable = AIChatUsageUtils.isRecoverableError(
          AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED
        )

        expect(isRecoverable).toBe(true)
      })

      it('プラン制限エラーは回復可能と判定する', () => {
        const isRecoverable = AIChatUsageUtils.isRecoverableError(
          AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION
        )

        expect(isRecoverable).toBe(true)
      })

      it('システムエラーは回復不可能と判定する', () => {
        const isRecoverable = AIChatUsageUtils.isRecoverableError(
          AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR
        )

        expect(isRecoverable).toBe(false)
      })
    })

    describe('formatUsageDisplay', () => {
      it('通常の利用状況を正しくフォーマットする', () => {
        const display = AIChatUsageUtils.formatUsageDisplay(5, 10)

        expect(display).toBe('5/10')
      })

      it('利用回数が0の場合を正しくフォーマットする', () => {
        const display = AIChatUsageUtils.formatUsageDisplay(0, 10)

        expect(display).toBe('0/10')
      })

      it('無制限プランを正しくフォーマットする', () => {
        const display = AIChatUsageUtils.formatUsageDisplay(999, -1)

        expect(display).toBe('無制限')
      })
    })

    describe('getUsageStatusColor', () => {
      it('利用回数が十分な場合、緑色を返す', () => {
        const color = AIChatUsageUtils.getUsageStatusColor(8, 10)

        expect(color).toBe('text-green-600')
      })

      it('利用回数が少ない場合、オレンジ色を返す', () => {
        const color = AIChatUsageUtils.getUsageStatusColor(2, 10) // 20%

        expect(color).toBe('text-orange-600')
      })

      it('利用回数が0の場合、赤色を返す', () => {
        const color = AIChatUsageUtils.getUsageStatusColor(0, 10)

        expect(color).toBe('text-red-600')
      })

      it('無制限プランの場合、緑色を返す', () => {
        const color = AIChatUsageUtils.getUsageStatusColor(999, -1)

        expect(color).toBe('text-green-600')
      })
    })
  })

  describe('エラー統合テスト', () => {
    it('エラーコードと対応するメッセージが一致する', () => {
      const errorCodes = Object.values(AI_CHAT_USAGE_ERROR_CODES)

      errorCodes.forEach(errorCode => {
        const simpleMessage = AIChatUsageUtils.getErrorMessage(errorCode, 'simple')
        const detailedMessage = AIChatUsageUtils.getErrorMessage(errorCode, 'detailed')
        const placeholderMessage = AIChatUsageUtils.getErrorMessage(errorCode, 'placeholder')
        const title = AIChatUsageUtils.getErrorTitle(errorCode)
        const actionText = AIChatUsageUtils.getErrorActionText(errorCode)

        expect(simpleMessage).toBeTruthy()
        expect(detailedMessage).toBeTruthy()
        expect(placeholderMessage).toBeTruthy()
        expect(title).toBeTruthy()

        // Action text can be null for some error types
        if (errorCode !== AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR) {
          expect(actionText).toBeTruthy()
        }
      })
    })

    it('すべてのエラーコードが定義されている', () => {
      expect(AI_CHAT_USAGE_ERROR_CODES.USAGE_LIMIT_EXCEEDED).toBe('USAGE_LIMIT_EXCEEDED')
      expect(AI_CHAT_USAGE_ERROR_CODES.PLAN_RESTRICTION).toBe('PLAN_RESTRICTION')
      expect(AI_CHAT_USAGE_ERROR_CODES.SYSTEM_ERROR).toBe('SYSTEM_ERROR')
    })

    it('エラーメッセージが日本語で提供される', () => {
      const errorCodes = Object.values(AI_CHAT_USAGE_ERROR_CODES)

      errorCodes.forEach(errorCode => {
        const message = AIChatUsageUtils.getErrorMessage(errorCode, 'simple')

        // Check if message contains Japanese characters
        expect(message).toMatch(/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/)
      })
    })
  })

  describe('境界値テスト', () => {
    it('極端な値でも適切に動作する', () => {
      // Very large numbers
      expect(AIChatUsageUtils.formatUsageDisplay(999999, 1000000)).toBe('999999/1000000')
      expect(AIChatUsageUtils.getUsageStatusColor(999999, 1000000)).toBe('text-green-600')

      // Zero values
      expect(AIChatUsageUtils.formatUsageDisplay(0, 0)).toBe('0/0')
      // When dailyLimit is 0, usageRatio becomes NaN, which doesn't match <= 0 condition
      // This results in the default green color
      expect(AIChatUsageUtils.getUsageStatusColor(0, 0)).toBe('text-green-600')

      // Negative values (edge case)
      expect(AIChatUsageUtils.formatUsageDisplay(-1, 10)).toBe('-1/10')
      expect(AIChatUsageUtils.getUsageStatusColor(-1, 10)).toBe('text-red-600')
    })

    it('時刻計算で極端な値を処理する', () => {
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2024-01-01T12:00:00Z'))

      // Very far future
      const farFuture = '2025-01-01T12:00:00Z'
      const timeUntil = AIChatUsageUtils.getTimeUntilReset(farFuture)
      expect(timeUntil).toMatch(/時間後$/)

      // Very far past
      const farPast = '2023-01-01T12:00:00Z'
      const timePast = AIChatUsageUtils.getTimeUntilReset(farPast)
      expect(timePast).toBe('まもなくリセット')

      vi.useRealTimers()
    })
  })
})