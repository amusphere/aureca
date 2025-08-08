/**
 * Tests for UsageDisplay component
 * Tests responsive design, accessibility, and 2-plan system support
 * Updated for new API interface and responsive design requirements
 */

import { render, screen, cleanup } from '@testing-library/react'
import { describe, expect, it, vi, afterEach } from 'vitest'
import UsageDisplay from '../../../components/components/ui/usage-display'
import type { AIChatUsageError } from '@/types/AIChatUsage'

// Ensure proper cleanup between tests
afterEach(() => {
  cleanup()
})

describe('UsageDisplay', () => {
  describe('Standard Plan Display', () => {
    it('displays usage information correctly for standard plan', () => {
      render(
        <UsageDisplay
          currentUsage={3}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )

      expect(screen.getByText('Standardプラン')).toBeInTheDocument()
      expect(screen.getByText('3/10回使用')).toBeInTheDocument()
      expect(screen.getByText('残り7回')).toBeInTheDocument()
    })

    it('displays compact variant correctly', () => {
      render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          variant="compact"
        />
      )

      expect(screen.getByText('5/10')).toBeInTheDocument()
      expect(screen.getByText('Standardプラン')).toBeInTheDocument()
    })

    it('displays minimal variant correctly', () => {
      render(
        <UsageDisplay
          currentUsage={2}
          dailyLimit={10}
          planName="standard"
          variant="minimal"
        />
      )

      expect(screen.getByText('残り8回')).toBeInTheDocument() // remaining count
    })

    it('shows reset time when enabled', () => {
      const resetTime = '2024-01-02T00:00:00Z'
      render(
        <UsageDisplay
          currentUsage={3}
          dailyLimit={10}
          planName="standard"
          showResetTime={true}
          resetTime={resetTime}
        />
      )

      expect(screen.getByText(/リセット/)).toBeInTheDocument()
    })

    it('displays correct status badge for different usage levels', () => {
      // Normal usage
      const { rerender } = render(
        <UsageDisplay
          currentUsage={2}
          dailyLimit={10}
          planName="standard"
        />
      )
      expect(screen.getByText('利用可能')).toBeInTheDocument()

      // At limit
      rerender(
        <UsageDisplay
          currentUsage={10}
          dailyLimit={10}
          planName="standard"
        />
      )
      expect(screen.getByText('上限達成')).toBeInTheDocument()
    })
  })

  describe('Free Plan Display', () => {
    it('displays free plan restrictions correctly', () => {
      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          variant="detailed"
        />
      )

      expect(screen.getByText('Freeプラン')).toBeInTheDocument()
      expect(screen.getByText('利用不可')).toBeInTheDocument()
    })

    it('shows upgrade message for free plan', () => {
      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          variant="detailed"
        />
      )

      expect(screen.getByText(/standardプランにアップグレード/)).toBeInTheDocument()
    })

    it('displays free plan in compact variant', () => {
      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          variant="compact"
        />
      )

      expect(screen.getByText('Freeプラン')).toBeInTheDocument()
      expect(screen.getByText('利用不可')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('displays loading skeleton when loading', () => {
      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={10}
          planName="standard"
          loading={true}
        />
      )

      // Check for skeleton elements instead of text
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
      expect(document.querySelector('[data-slot="skeleton"]')).toBeInTheDocument()
    })

    it('displays loading state in different variants', () => {
      const { rerender } = render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={10}
          planName="standard"
          variant="compact"
          loading={true}
        />
      )

      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()

      rerender(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={10}
          planName="standard"
          variant="minimal"
          loading={true}
        />
      )

      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    const mockError: AIChatUsageError = {
      error: '本日の利用回数上限（10回）に達しました',
      error_code: 'USAGE_LIMIT_EXCEEDED',
      remaining_count: 0,
      reset_time: '2024-01-02T00:00:00Z'
    }

    it('displays error message correctly', () => {
      render(
        <UsageDisplay
          currentUsage={10}
          dailyLimit={10}
          planName="standard"
          error={mockError}
        />
      )

      // The component shows detailed error message
      expect(screen.getByText(/本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。/)).toBeInTheDocument()
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('displays plan restriction error', () => {
      const planError: AIChatUsageError = {
        error: 'freeプランではAIChatをご利用いただけません',
        error_code: 'PLAN_RESTRICTION',
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z'
      }

      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          error={planError}
        />
      )

      // The component shows detailed error message
      expect(screen.getByText(/freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。/)).toBeInTheDocument()
    })

    it('displays system error', () => {
      const systemError: AIChatUsageError = {
        error: '一時的なエラーが発生しました',
        error_code: 'SYSTEM_ERROR',
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z'
      }

      render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          error={systemError}
        />
      )

      // The component shows detailed error message
      expect(screen.getByText(/一時的なエラーが発生しました。しばらく後にお試しください。/)).toBeInTheDocument()
    })

    it('displays Clerk API error', () => {
      const clerkError: AIChatUsageError = {
        error: 'プラン情報の取得に失敗しました',
        error_code: 'CLERK_API_ERROR',
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z'
      }

      render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          error={clerkError}
        />
      )

      // The component shows detailed error message
      expect(screen.getByText(/プラン情報の取得に失敗しました。しばらく後にお試しください。/)).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    it('applies custom className correctly', () => {
      const { container } = render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          className="custom-class"
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })

    it('renders with responsive classes', () => {
      const { container } = render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )

      // Check for responsive classes (these would be in the actual component)
      expect(container.firstChild).toHaveClass('w-full')
    })
  })

  describe('Accessibility', () => {
    it('provides proper ARIA labels for progress bar', () => {
      render(
        <UsageDisplay
          currentUsage={3}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )

      // Check for accessibility attributes on progress bar
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-label')
    })

    it('provides screen reader friendly text', () => {
      render(
        <UsageDisplay
          currentUsage={3}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )

      // Check for screen reader text
      expect(screen.getByText('Standardプラン')).toBeInTheDocument()
    })

    it('announces errors to screen readers', () => {
      const mockError: AIChatUsageError = {
        error: '本日の利用回数上限（10回）に達しました',
        error_code: 'USAGE_LIMIT_EXCEEDED',
        remaining_count: 0,
        reset_time: '2024-01-02T00:00:00Z'
      }

      render(
        <UsageDisplay
          currentUsage={10}
          dailyLimit={10}
          planName="standard"
          error={mockError}
        />
      )

      const alertElement = screen.getByRole('alert')
      expect(alertElement).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles zero daily limit correctly', () => {
      render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
        />
      )

      expect(screen.getByText('利用不可')).toBeInTheDocument()
    })

    it('handles negative values gracefully', () => {
      render(
        <UsageDisplay
          currentUsage={-1}
          dailyLimit={10}
          planName="standard"
        />
      )

      // Should handle negative values gracefully
      expect(screen.getByText(/10/)).toBeInTheDocument()
    })

    it('handles usage exceeding limit', () => {
      render(
        <UsageDisplay
          currentUsage={15}
          dailyLimit={10}
          planName="standard"
        />
      )

      // Should show 0 remaining when usage exceeds limit
      expect(screen.getByText('残り0回')).toBeInTheDocument()
      expect(screen.getByText('上限達成')).toBeInTheDocument()
    })

    it('handles missing reset time', () => {
      render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          showResetTime={true}
          resetTime={undefined}
        />
      )

      // Should handle missing reset time gracefully
      expect(screen.getByText(/明日の00:00にリセット/)).toBeInTheDocument()
    })

    it('handles invalid reset time format', () => {
      render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          showResetTime={true}
          resetTime="invalid-date"
        />
      )

      // Should handle invalid date gracefully - shows the invalid date as-is
      expect(screen.getByText(/invalid-dateにリセット/)).toBeInTheDocument()
    })
  })

  describe('Progress Bar', () => {
    it('displays progress bar for standard plan', () => {
      render(
        <UsageDisplay
          currentUsage={3}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )

      // Check for progress bar elements
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
      expect(progressBar).toHaveAttribute('aria-valuenow', '3') // Current usage
      expect(progressBar).toHaveAttribute('aria-valuemax', '10') // Daily limit
    })

    it('shows correct progress bar color based on usage', () => {
      // Low usage (green)
      const { rerender, container } = render(
        <UsageDisplay
          currentUsage={2}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )
      expect(container.querySelector('[role="progressbar"]')).toHaveClass('bg-green-500')

      // High usage (yellow/orange)
      rerender(
        <UsageDisplay
          currentUsage={8}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )
      expect(container.querySelector('[role="progressbar"]')).toHaveClass('bg-yellow-500')

      // At limit (red)
      rerender(
        <UsageDisplay
          currentUsage={10}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )
      expect(container.querySelector('[role="progressbar"]')).toHaveClass('bg-red-500')
    })

    it('does not show progress bar for free plan', () => {
      const { container } = render(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          variant="detailed"
        />
      )

      expect(container.querySelector('[role="progressbar"]')).not.toBeInTheDocument()
    })
  })

  describe('Icons', () => {
    it('displays appropriate icons for different states', () => {
      // Standard plan with usage - should show check circle for remaining usage
      const { rerender } = render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )
      // Check for Lucide icons by their SVG class names
      expect(document.querySelector('.lucide-zap')).toBeInTheDocument()
      expect(document.querySelector('.lucide-circle-check-big')).toBeInTheDocument()

      // At limit - should show alert circle
      rerender(
        <UsageDisplay
          currentUsage={10}
          dailyLimit={10}
          planName="standard"
          variant="detailed"
        />
      )
      expect(document.querySelector('.lucide-circle-alert')).toBeInTheDocument()

      // Free plan - should show zap icon for plan
      rerender(
        <UsageDisplay
          currentUsage={0}
          dailyLimit={0}
          planName="free"
          variant="detailed"
        />
      )
      expect(document.querySelector('.lucide-zap')).toBeInTheDocument()
    })
  })

  describe('Time Display', () => {
    it('displays reset time correctly', () => {
      const resetTime = '2024-01-02T00:00:00Z'
      const { container } = render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          showResetTime={true}
          resetTime={resetTime}
        />
      )

      // Should display the reset time as provided
      expect(container.textContent).toContain('2024-01-02T00:00:00Zにリセット')
    })

    it('shows default reset message when no time provided', () => {
      const { container } = render(
        <UsageDisplay
          currentUsage={5}
          dailyLimit={10}
          planName="standard"
          showResetTime={true}
        />
      )

      expect(container.textContent).toContain('明日の00:00にリセット')
    })
  })
})