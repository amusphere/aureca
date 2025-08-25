import { useUser } from '@/components/hooks/useUser';
import { UserWithSubscription } from '@/types/User';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React, { ReactNode } from 'react';
import { vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries for tests
        gcTime: 0, // Disable cache persistence for tests
        staleTime: 0, // Always consider data stale in tests
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
      },
    },
  });

  return function TestWrapper({ children }: { children: ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useUser', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should initialize with loading state', () => {
    mockFetch.mockImplementation(() => new Promise(() => { })); // Never resolves

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.isPremium).toBe(false);
  });

  it('should fetch user data successfully', async () => {
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
        stripeSubscriptionId: 'sub_test',
        stripePriceId: 'price_test',
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    });

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isPremium).toBe(true);
    expect(result.current.error).toBe(null);
  });

  it('should handle user without subscription', async () => {
    const mockUser: UserWithSubscription = {
      id: 1,
      uuid: 'test-uuid',
      email: 'test@example.com',
      name: 'Test User',
      clerkSub: 'clerk-sub',
      stripeCustomerId: null,
      createdAt: Date.now() / 1000,
      subscription: null,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    });

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle 401 unauthorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    });

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle API errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ message: 'Server error' }),
    });

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe('Server error');
  });

  it('should provide refreshUser function', async () => {
    const mockUser: UserWithSubscription = {
      id: 1,
      uuid: 'test-uuid',
      email: 'test@example.com',
      name: 'Test User',
      clerkSub: 'clerk-sub',
      stripeCustomerId: 'cus_test',
      createdAt: Date.now() / 1000,
      subscription: {
        isPremium: false,
        planName: null,
        status: null,
        currentPeriodEnd: null,
        cancelAtPeriodEnd: false,
        stripeSubscriptionId: null,
        stripePriceId: null,
      },
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify refreshUser function exists and is callable
    expect(typeof result.current.refreshUser).toBe('function');

    // Call refreshUser - it should not throw
    await expect(result.current.refreshUser()).resolves.not.toThrow();

    // Verify fetch was called at least twice (initial + refresh)
    expect(mockFetch).toHaveBeenCalledTimes(3); // React Query may call multiple times due to invalidation
  });

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe('Network error');
  });

  it('should use cached data for subsequent renders', async () => {
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

    const wrapper = createWrapper();

    // First render
    const { result: result1 } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result1.current.isLoading).toBe(false);
    });

    expect(result1.current.user).toEqual(mockUser);
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Second render should use cached data
    const { result: result2 } = renderHook(() => useUser(), { wrapper });

    // Should immediately have data from cache
    expect(result2.current.user).toEqual(mockUser);
    expect(result2.current.isLoading).toBe(false);

    // Should not make another API call
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});