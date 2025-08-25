"use client";

import { useState, useCallback } from 'react';
import { UseSubscriptionReturn, SubscriptionLoadingStates, SubscriptionErrorStates } from '@/types/StripeUi';
import { CheckoutSessionRequest, CheckoutSessionResponse, CustomerPortalResponse } from '@/types/Subscription';
import { formatErrorMessage, logError, isRetryableError, getSuggestedActions } from '@/utils/errorHandling';

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

        // Log the error for debugging
        logError(errorData, 'createCheckoutSession');

        // Create a proper error object
        const error = {
          response: {
            status: response.status,
            data: errorData,
          },
        };

        throw error;
      }

      const data: CheckoutSessionResponse = await response.json();

      // Redirect to Stripe Checkout
      if (data.url) {
        window.location.href = data.url;
      } else {
        const error = {
          error: {
            code: 'CHECKOUT_URL_MISSING',
            message: 'No checkout URL received from server',
          },
        };
        logError(error, 'createCheckoutSession - missing URL');
        throw error;
      }
    } catch (err) {
      // Format the error message using our error handling utilities
      const errorMessage = formatErrorMessage(err);
      const retryable = isRetryableError(err);
      const actions = getSuggestedActions(err);

      setErrors(prev => ({
        ...prev,
        checkout: {
          message: errorMessage,
          isRetryable: retryable,
          suggestedActions: actions,
        },
      }));

      // Log the error for debugging
      logError(err, 'createCheckoutSession');
    } finally {
      setLoading(prev => ({ ...prev, creatingCheckout: false }));
    }
  }, [clearError]);

  /**
   * Open Stripe Customer Portal for subscription management
   */
  const openCustomerPortal = useCallback(async (returnUrl?: string) => {
    try {
      setLoading(prev => ({ ...prev, openingPortal: true }));
      clearError('portal');

      const requestData = {
        return_url: returnUrl || `${window.location.origin}/subscription`,
      };

      const response = await fetch('/api/stripe/create-portal-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        // Log the error for debugging
        logError(errorData, 'openCustomerPortal');

        // Create a proper error object
        const error = {
          response: {
            status: response.status,
            data: errorData,
          },
        };

        throw error;
      }

      const data: CustomerPortalResponse = await response.json();

      // Redirect to Stripe Customer Portal
      if (data.url) {
        window.location.href = data.url;
      } else {
        const error = {
          error: {
            code: 'PORTAL_URL_MISSING',
            message: 'No portal URL received from server',
          },
        };
        logError(error, 'openCustomerPortal - missing URL');
        throw error;
      }
    } catch (err) {
      // Format the error message using our error handling utilities
      const errorMessage = formatErrorMessage(err);
      const retryable = isRetryableError(err);
      const actions = getSuggestedActions(err);

      setErrors(prev => ({
        ...prev,
        portal: {
          message: errorMessage,
          isRetryable: retryable,
          suggestedActions: actions,
        },
      }));

      // Log the error for debugging
      logError(err, 'openCustomerPortal');
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