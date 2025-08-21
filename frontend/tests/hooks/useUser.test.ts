import { renderHook, waitFor } from '@testing-library/react';
import { useUser } from '@/components/hooks/useUser';
import { UserWithSubscription } from '@/types/User';
import { vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useUser', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should initialize with loading state', () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { result } = renderHook(() => useUser());

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

    const { result } = renderHook(() => useUser());

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

    const { result } = renderHook(() => useUser());

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

    const { result } = renderHook(() => useUser());

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

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe('Server error');
  });

  it('should refresh user data when refreshUser is called', async () => {
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

    const updatedUser: UserWithSubscription = {
      ...mockUser,
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

    // First call returns user without premium
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isPremium).toBe(false);

    // Second call returns user with premium
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => updatedUser,
    });

    // Call refreshUser
    await result.current.refreshUser();

    await waitFor(() => {
      expect(result.current.isPremium).toBe(true);
    });

    expect(result.current.user?.subscription?.planName).toBe('Pro Plan');
  });

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe('Network error');
  });
});