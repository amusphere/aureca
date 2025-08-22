import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { PremiumGuard, InlinePremiumGuard } from '@/components/components/commons/PremiumGuard';
import { useUser } from '@/components/hooks/useUser';
import { vi } from 'vitest';

// Mock the hooks
vi.mock('@/components/hooks/useUser');
vi.mock('next/navigation');

const mockUseUser = vi.mocked(useUser);
const mockUseRouter = vi.mocked(useRouter);
const mockPush = vi.fn();

describe('PremiumGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    } as any);
  });

  describe('when loading', () => {
    it('should show loading spinner', () => {
      mockUseUser.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        isPremium: false,
        refreshUser: vi.fn(),
      });

      const { container } = render(
        <PremiumGuard>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      // Check for the loading spinner by looking for the animate-spin class
      expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  describe('when user is not authenticated', () => {
    it('should not render anything', () => {
      mockUseUser.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isPremium: false,
        refreshUser: vi.fn(),
      });

      const { container } = render(
        <PremiumGuard>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('when user has premium access', () => {
    it('should render children', () => {
      mockUseUser.mockReturnValue({
        user: {
          id: 1,
          uuid: 'test-uuid',
          email: 'test@example.com',
          name: 'Test User',
          clerkSub: null,
          stripeCustomerId: 'cus_test',
          createdAt: Date.now(),
          subscription: {
            isPremium: true,
            planName: 'Pro',
            status: 'active',
            currentPeriodEnd: Date.now() + 86400000,
            cancelAtPeriodEnd: false,
            stripeSubscriptionId: 'sub_test',
            stripePriceId: 'price_test',
          },
        },
        isLoading: false,
        error: null,
        isPremium: true,
        refreshUser: vi.fn(),
      });

      render(
        <PremiumGuard>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(screen.getByText('Premium Content')).toBeInTheDocument();
    });
  });

  describe('when user does not have premium access', () => {
    beforeEach(() => {
      mockUseUser.mockReturnValue({
        user: {
          id: 1,
          uuid: 'test-uuid',
          email: 'test@example.com',
          name: 'Test User',
          clerkSub: null,
          stripeCustomerId: 'cus_test',
          createdAt: Date.now(),
          subscription: {
            isPremium: false,
            planName: null,
            status: null,
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            stripeSubscriptionId: null,
            stripePriceId: null,
          },
        },
        isLoading: false,
        error: null,
        isPremium: false,
        refreshUser: vi.fn(),
      });
    });

    it('should show upgrade prompt by default', () => {
      render(
        <PremiumGuard>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(screen.getByText('プレミアム機能')).toBeInTheDocument();
      expect(screen.getByText('この機能を利用するには有料プランへのアップグレードが必要です。')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /有料プランにアップグレード/ })).toBeInTheDocument();
    });

    it('should show custom upgrade message', () => {
      render(
        <PremiumGuard upgradeMessage="カスタムメッセージ">
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(screen.getByText('カスタムメッセージ')).toBeInTheDocument();
    });

    it('should show custom fallback when provided', () => {
      render(
        <PremiumGuard fallback={<div>Custom Fallback</div>}>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(screen.getByText('Custom Fallback')).toBeInTheDocument();
      expect(screen.queryByText('プレミアム機能')).not.toBeInTheDocument();
    });

    it('should not show anything when showUpgrade is false', () => {
      const { container } = render(
        <PremiumGuard showUpgrade={false}>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      expect(container.firstChild).toBeNull();
    });

    it('should navigate to subscription page when upgrade button is clicked', async () => {
      render(
        <PremiumGuard>
          <div>Premium Content</div>
        </PremiumGuard>
      );

      const upgradeButton = screen.getByRole('button', { name: /有料プランにアップグレード/ });
      fireEvent.click(upgradeButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/subscription');
      });
    });
  });
});

describe('InlinePremiumGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    } as unknown);
  });

  describe('when user has premium access', () => {
    it('should render children', () => {
      mockUseUser.mockReturnValue({
        user: {
          id: 1,
          uuid: 'test-uuid',
          email: 'test@example.com',
          name: 'Test User',
          clerkSub: null,
          stripeCustomerId: 'cus_test',
          createdAt: Date.now(),
          subscription: {
            isPremium: true,
            planName: 'Pro',
            status: 'active',
            currentPeriodEnd: Date.now() + 86400000,
            cancelAtPeriodEnd: false,
            stripeSubscriptionId: 'sub_test',
            stripePriceId: 'price_test',
          },
        },
        isLoading: false,
        error: null,
        isPremium: true,
        refreshUser: vi.fn(),
      });

      render(
        <InlinePremiumGuard>
          <button>Premium Button</button>
        </InlinePremiumGuard>
      );

      expect(screen.getByRole('button', { name: 'Premium Button' })).toBeInTheDocument();
    });
  });

  describe('when user does not have premium access', () => {
    it('should show inline upgrade button', () => {
      mockUseUser.mockReturnValue({
        user: {
          id: 1,
          uuid: 'test-uuid',
          email: 'test@example.com',
          name: 'Test User',
          clerkSub: null,
          stripeCustomerId: 'cus_test',
          createdAt: Date.now(),
          subscription: {
            isPremium: false,
            planName: null,
            status: null,
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            stripeSubscriptionId: null,
            stripePriceId: null,
          },
        },
        isLoading: false,
        error: null,
        isPremium: false,
        refreshUser: vi.fn(),
      });

      render(
        <InlinePremiumGuard>
          <button>Premium Button</button>
        </InlinePremiumGuard>
      );

      expect(screen.getByRole('button', { name: /プレミアム機能/ })).toBeInTheDocument();
    });

    it('should navigate to subscription page when clicked', async () => {
      mockUseUser.mockReturnValue({
        user: {
          id: 1,
          uuid: 'test-uuid',
          email: 'test@example.com',
          name: 'Test User',
          clerkSub: null,
          stripeCustomerId: 'cus_test',
          createdAt: Date.now(),
          subscription: {
            isPremium: false,
            planName: null,
            status: null,
            currentPeriodEnd: null,
            cancelAtPeriodEnd: false,
            stripeSubscriptionId: null,
            stripePriceId: null,
          },
        },
        isLoading: false,
        error: null,
        isPremium: false,
        refreshUser: vi.fn(),
      });

      render(
        <InlinePremiumGuard>
          <button>Premium Button</button>
        </InlinePremiumGuard>
      );

      const upgradeButton = screen.getByRole('button', { name: /プレミアム機能/ });
      fireEvent.click(upgradeButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/subscription');
      });
    });
  });
});