import { useUser } from '@/components/hooks/useUser';
import { UserWithSubscription } from '@/types/User';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, it } from 'node:test';
import React from 'react';
import { vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Test component that uses the useUser hook
function TestComponent() {
  const { user, isLoading, error, isPremium, refreshUser } = useUser();

  if (isLoading) {
    return <div data-testid="loading">Loading...</div>;
  }

  if (error) {
    return <div data-testid="error">{error}</div>;
  }

  return (
    <div>
      <div data-testid="user-email">{user?.email || 'No email'}</div>
      <div data-testid="premium-status">{isPremium ? 'Premium' : 'Free'}</div>
      <div data-testid="plan-name">{user?.subscription?.planName || 'No plan'}</div>
      <button data-testid="refresh-button" onClick={refreshUser}>
        Refresh
      </button>
    </div>
  );
}

// Test wrapper with QueryClient
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe('useUser Integration Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should render user data correctly in a component', async () => {
    const mockUser: UserWithSubscription = {
      id: 1,
      uuid: 'test-uuid',
      email: 'test@example.com',
      name: 'Test User',
      clerkSub: 'clerk-sub',
      stripeCustomerId: 'cus_test',
      createdAt: Date.now() / 1000,
      subscription: {
        isPremium: true,
        planName: 'Pro Plan',
        status: 'active',
        currentPeriodEnd: Date.now() / 1000 + 86400,
        cancelAtPeriodEnd: false,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    // Initially should show loading
    expect(screen.getByTestId('loading')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });

    expect(screen.getByTestId('premium-status')).toHaveTextContent('Premium');
    expect(screen.getByTestId('plan-name')).toHaveTextContent('Pro Plan');
  });

  it('should handle free user correctly', async () => {
    const mockUser: UserWithSubscription = {
      id: 1,
      uuid: 'test-uuid',
      email: 'free@example.com',
      name: 'Free User',
      clerkSub: 'clerk-sub',
      stripeCustomerId: null,
      createdAt: Date.now() / 1000,
      subscription: null,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('free@example.com');
    });

    expect(screen.getByTestId('premium-status')).toHaveTextContent('Free');
    expect(screen.getByTestId('plan-name')).toHaveTextContent('No plan');
  });

  it('should handle errors correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ message: 'Server error' }),
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Server error');
    });
  });

  it('should handle 401 unauthorized without showing error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    });

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('No email');
    });

    expect(screen.getByTestId('premium-status')).toHaveTextContent('Free');
    expect(screen.getByTestId('plan-name')).toHaveTextContent('No plan');
  });
});