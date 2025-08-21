/**
 * Integration test for useUser hook
 * Tests the hook with actual API calls (mocked at the fetch level)
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useUser } from '@/components/hooks/useUser';
import { vi } from 'vitest';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { it } from 'date-fns/locale';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock fetch for integration testing
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useUser Integration Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should integrate with the /api/users/me endpoint correctly', async () => {
    const mockApiResponse = {
      id: 1,
      uuid: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      clerkSub: 'clerk_123',
      stripeCustomerId: 'cus_123',
      createdAt: 1640995200,
      subscription: {
        isPremium: true,
        planName: 'Pro Plan',
        status: 'active',
        currentPeriodEnd: 1672531200,
        cancelAtPeriodEnd: false,
        stripeSubscriptionId: 'sub_123',
        stripePriceId: 'price_123',
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse,
    });

    const { result } = renderHook(() => useUser());

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBe(null);

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify the hook correctly processes the API response
    expect(result.current.user).toEqual(mockApiResponse);
    expect(result.current.isPremium).toBe(true);
    expect(result.current.error).toBe(null);

    // Verify the correct API call was made
    expect(mockFetch).toHaveBeenCalledWith('/api/users/me', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
  });

  it('should handle subscription status changes correctly', async () => {
    // First response: user without premium
    const initialResponse = {
      id: 1,
      uuid: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      clerkSub: 'clerk_123',
      stripeCustomerId: 'cus_123',
      createdAt: 1640995200,
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

    // Second response: user with premium after subscription
    const updatedResponse = {
      ...initialResponse,
      subscription: {
        isPremium: true,
        planName: 'Pro Plan',
        status: 'active',
        currentPeriodEnd: 1672531200,
        cancelAtPeriodEnd: false,
        stripeSubscriptionId: 'sub_123',
        stripePriceId: 'price_123',
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => initialResponse,
    });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Initially not premium
    expect(result.current.isPremium).toBe(false);
    expect(result.current.user?.subscription?.planName).toBe(null);

    // Mock the refresh call
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => updatedResponse,
    });

    // Refresh user data
    await result.current.refreshUser();

    // Wait for the refresh to complete
    await waitFor(() => {
      expect(result.current.isPremium).toBe(true);
    });

    expect(result.current.user?.subscription?.planName).toBe('Pro Plan');
    expect(result.current.user?.subscription?.status).toBe('active');
  });

  it('should handle authentication errors gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should handle 401 by setting user to null without error
    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle server errors with proper error messages', async () => {
    const errorResponse = {
      message: 'Internal server error',
    };

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => errorResponse,
    });

    const { result } = renderHook(() => useUser());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBe(null);
    expect(result.current.isPremium).toBe(false);
    expect(result.current.error).toBe('Internal server error');
  });
});