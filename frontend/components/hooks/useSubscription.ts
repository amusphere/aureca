"use client";

import { useState, useCallback } from 'react';
import { UseSubscriptionReturn, SubscriptionLoadingStates, SubscriptionErrorStates } from '@/types/stripe-ui';
import { CheckoutSessionRequest, CheckoutSessionResponse, CustomerPortalResponse } from '@/types/Subscription';

/**
 * Custom hook for managing Stripe subscription operations
 * Provides checkout session creation and customer portal access
 */
export function useSubscription(): UseSubscriptionReturn {
  const [loading, setLoading] = useState<SubscriptionLoadingStates>({
    creatingCheckout: false,
    openingPortal: false,
    refreshingUser: false,
  });

  const [errors, setErrors] = useState<SubscriptionErrorStates>({
    checkout: null,
    portal: null,
    user: null,
  });

  /**
   * Clear a specific error type
   */
  const clearError = useCallback((type: keyof SubscriptionErrorStates) => {
    setErrors(prev => ({
      ...prev,
      [type]: null,
    }));
  }, []);

  /**
   * Create a Stripe checkout session and redirect to Stripe Checkout
   */
  const createCheckoutSession = useCallback(async (priceId: string) => {
    try {
      setLoading(prev => ({ ...prev, creatingCheckout: true }));
      clearError('checkout');

      const requestData: CheckoutSessionRequest = {
        priceId,
        successUrl: `${window.location.origin}/subscription?success=true`,
        cancelUrl: `${window.location.origin}/subscription?canceled=true`,
      };

      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: CheckoutSessionResponse = await response.json();

      // Redirect to Stripe Checkout
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error('No checkout URL received from server');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create checkout session';
      setErrors(prev => ({
        ...prev,
        checkout: errorMessage,
      }));
      console.error('Error creating checkout session:', err);
    } finally {
      setLoading(prev => ({ ...prev, creatingCheckout: false }));
    }
  }, [clearError]);

  /**
   * Open Stripe Customer Portal for subscription management
   */
  const openCustomerPortal = useCallback(async () => {
    try {
      setLoading(prev => ({ ...prev, openingPortal: true }));
      clearError('portal');

      const response = await fetch('/api/stripe/create-portal-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: CustomerPortalResponse = await response.json();

      // Redirect to Stripe Customer Portal
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error('No portal URL received from server');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to open customer portal';
      setErrors(prev => ({
        ...prev,
        portal: errorMessage,
      }));
      console.error('Error opening customer portal:', err);
    } finally {
      setLoading(prev => ({ ...prev, openingPortal: false }));
    }
  }, [clearError]);

  return {
    createCheckoutSession,
    openCustomerPortal,
    loading,
    errors,
    clearError,
  };
}