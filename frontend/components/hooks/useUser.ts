"use client";

import { useState, useEffect, useCallback } from 'react';
import { UserWithSubscription } from '@/types/User';
import { UseUserReturn } from '@/types/stripe-ui';

/**
 * Custom hook for managing user data with subscription information
 * Provides caching, refresh functionality, and isPremium determination
 */
export function useUser(): UseUserReturn {
  const [user, setUser] = useState<UserWithSubscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Determine if user has premium access based on subscription status
   */
  const isPremium = user?.subscription?.isPremium ?? false;

  /**
   * Fetch user data from the API
   */
  const fetchUser = useCallback(async () => {
    try {
      setError(null);

      const response = await fetch('/api/users/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          // User is not authenticated
          setUser(null);
          return;
        }

        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const userData: UserWithSubscription = await response.json();
      setUser(userData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user data';
      setError(errorMessage);
      console.error('Error fetching user:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh user data - can be called manually to update subscription status
   */
  const refreshUser = useCallback(async () => {
    setIsLoading(true);
    await fetchUser();
  }, [fetchUser]);

  /**
   * Initial data fetch on mount
   */
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return {
    user,
    isLoading,
    error,
    isPremium,
    refreshUser,
  };
}