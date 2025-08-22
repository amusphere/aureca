import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { useUser } from '@/components/hooks/useUser';
import { useSubscription } from '@/components/hooks/useSubscription';
import SubscriptionPage from '../../app/(authed)/subscription/page';

// Mock the hooks
vi.mock('@/components/hooks/useUser');
vi.mock('@/components/hooks/useSubscription');

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

const mockUseUser = vi.mocked(useUser);
const mockUseSubscription = vi.mocked(useSubscription);

describe('SubscriptionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock environment variables
    vi.stubEnv('NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY', 'pk_test_123');
    vi.stubEnv('NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID', 'prctbl_123');

    // Default mock implementations
    mockUseSubscription.mockReturnValue({
      createCheckoutSession: vi.fn(),
      openCustomerPortal: vi.fn(),
      loading: {
        creatingCheckout: false,
        openingPortal: false,
        refreshingUser: false,
      },
      errors: {
        checkout: null,
        portal: null,
        user: null,
      },
      clearError: vi.fn(),
    });
  });

  it('shows loading state when user data is loading', () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: true,
      error: null,
      isPremium: false,
      refreshUser: vi.fn(),
    });

    const { container } = render(<SubscriptionPage />);

    // Should show skeleton loading components
    const skeletonElements = container.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows free plan status for non-premium users', async () => {
    mockUseUser.mockReturnValue({
      user: {
        id: 1,
        uuid: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        clerkSub: null,
        stripeCustomerId: null,
        createdAt: Date.now() / 1000,
        subscription: null,
      },
      isLoading: false,
      error: null,
      isPremium: false,
      refreshUser: vi.fn(),
    });

    render(<SubscriptionPage />);

    await waitFor(() => {
      expect(screen.getByText('フリープラン')).toBeInTheDocument();
      expect(screen.getByText('プランを選択')).toBeInTheDocument();
    });
  });

  it('shows premium plan status for premium users', async () => {
    mockUseUser.mockReturnValue({
      user: {
        id: 1,
        uuid: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        clerkSub: null,
        stripeCustomerId: 'cus_123',
        createdAt: Date.now() / 1000,
        subscription: {
          isPremium: true,
          planName: 'Premium Plan',
          status: 'active',
          currentPeriodEnd: Math.floor(Date.now() / 1000) + 86400 * 30, // 30 days from now
          cancelAtPeriodEnd: false,
          stripeSubscriptionId: 'sub_123',
          stripePriceId: 'price_123',
        },
      },
      isLoading: false,
      error: null,
      isPremium: true,
      refreshUser: vi.fn(),
    });

    render(<SubscriptionPage />);

    await waitFor(() => {
      expect(screen.getByText('Premium Plan')).toBeInTheDocument();
      expect(screen.getByText('アクティブ')).toBeInTheDocument();
      expect(screen.getByText('請求情報を管理')).toBeInTheDocument();
    });
  });

  it('shows cancellation notice for canceled subscriptions', async () => {
    mockUseUser.mockReturnValue({
      user: {
        id: 1,
        uuid: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        clerkSub: null,
        stripeCustomerId: 'cus_123',
        createdAt: Date.now() / 1000,
        subscription: {
          isPremium: true,
          planName: 'Premium Plan',
          status: 'active',
          currentPeriodEnd: Math.floor(Date.now() / 1000) + 86400 * 30,
          cancelAtPeriodEnd: true,
          stripeSubscriptionId: 'sub_123',
          stripePriceId: 'price_123',
        },
      },
      isLoading: false,
      error: null,
      isPremium: true,
      refreshUser: vi.fn(),
    });

    render(<SubscriptionPage />);

    await waitFor(() => {
      expect(screen.getByText(/このサブスクリプションは.*にキャンセルされます/)).toBeInTheDocument();
    });
  });

  it('shows loading message when Stripe is not configured', async () => {
    mockUseUser.mockReturnValue({
      user: {
        id: 1,
        uuid: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        clerkSub: null,
        stripeCustomerId: null,
        createdAt: Date.now() / 1000,
        subscription: null,
      },
      isLoading: false,
      error: null,
      isPremium: false,
      refreshUser: vi.fn(),
    });

    render(<SubscriptionPage />);

    await waitFor(() => {
      // Should show either loading message or configuration error
      expect(
        screen.getByText('料金表を読み込み中...') ||
        screen.getByText(/Stripe.*設定/)
      ).toBeInTheDocument();
    });
  });

  it('handles responsive design classes', async () => {
    mockUseUser.mockReturnValue({
      user: {
        id: 1,
        uuid: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        clerkSub: null,
        stripeCustomerId: null,
        createdAt: Date.now() / 1000,
        subscription: null,
      },
      isLoading: false,
      error: null,
      isPremium: false,
      refreshUser: vi.fn(),
    });

    const { container } = render(<SubscriptionPage />);

    // Check for responsive classes
    const mainContainer = container.querySelector('.container');
    expect(mainContainer).toHaveClass('mx-auto', 'px-4', 'py-8', 'max-w-4xl');

    // Check for responsive grid classes
    const gridElements = container.querySelectorAll('.grid-cols-1.md\\:grid-cols-2');
    expect(gridElements.length).toBeGreaterThan(0);
  });
});