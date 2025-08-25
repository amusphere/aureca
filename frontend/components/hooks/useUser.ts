"use client";

import { UseUserReturn } from '@/types/StripeUi';
import { UserWithSubscription } from '@/types/User';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

/**
 * Query key for user data caching
 */
const USER_QUERY_KEY = ['user', 'me'] as const;

/**
 * Cache duration: 5 minutes (300 seconds) as specified in requirements
 */
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Fetch user data from the API
 */
async function fetchUserData(): Promise<UserWithSubscription | null> {
  const response = await fetch('/api/users/me', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      // User is not authenticated - return null instead of throwing
      return null;
    }

    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
  }

  const userData: UserWithSubscription = await response.json();
  return userData;
}

/**
 * Custom hook for managing user data with subscription information
 * Uses React Query for caching with 5-minute stale time
 * Provides refresh functionality and isPremium determination
 */
export function useUser(): UseUserReturn {
  const queryClient = useQueryClient();

  /**
   * React Query for user data with 5-minute client-side cache
   */
  const {
    data: user,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: USER_QUERY_KEY,
    queryFn: fetchUserData,
    staleTime: CACHE_DURATION, // Data is fresh for 5 minutes
    gcTime: CACHE_DURATION * 2, // Keep in cache for 10 minutes
    retry: (failureCount, error) => {
      // Don't retry on authentication errors
      if (error instanceof Error && error.message.includes('401')) {
        return false;
      }
      // In test environment, don't retry to make tests predictable
      if (process.env.NODE_ENV === 'test') {
        return false;
      }
      // Retry up to 2 times for other errors in production
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  });

  /**
   * Determine if user has premium access based on subscription status
   */
  const isPremium = user?.subscription?.isPremium ?? false;

  /**
   * Convert React Query error to string format
   */
  const error = queryError instanceof Error ? queryError.message : null;

  /**
   * Refresh user data - invalidates cache and refetches
   * This ensures fresh data from the server, bypassing cache
   */
  const refreshUser = useCallback(async (): Promise<void> => {
    try {
      // Invalidate the cache to ensure fresh data
      await queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
      // Refetch the data
      await refetch();
    } catch (err) {
      console.error('Error refreshing user data:', err);
      // Error will be handled by React Query and exposed through the error state
    }
  }, [queryClient, refetch]);

  return {
    user: user ?? null,
    isLoading,
    error,
    isPremium,
    refreshUser,
  };
}