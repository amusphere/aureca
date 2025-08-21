import { renderHook, act } from '@testing-library/react';
import { useSubscription } from '@/components/hooks/useSubscription';
import { vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  origin: 'http://localhost:3000',
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('useSubscription', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    mockLocation.href = '';
    console.error = vi.fn(); // Suppress console.error in tests
  });

  describe('createCheckoutSession', () => {
    it('should create checkout session and redirect on success', async () => {
      const mockResponse = {
        sessionId: 'cs_test_123',
        url: 'https://checkout.stripe.com/pay/cs_test_123',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.createCheckoutSession('price_test_123');
      });

      // Verify API call
      expect(mockFetch).toHaveBeenCalledWith('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          priceId: 'price_test_123',
          successUrl: 'http://localhost:3000/subscription?success=true',
          cancelUrl: 'http://localhost:3000/subscription?canceled=true',
        }),
      });

      // Verify redirect
      expect(mockLocation.href).toBe('https://checkout.stripe.com/pay/cs_test_123');

      // Verify no errors
      expect(result.current.errors.checkout).toBeNull();
      expect(result.current.loading.creatingCheckout).toBe(false);
    });

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'Invalid price ID';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ message: errorMessage }),
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.createCheckoutSession('invalid_price');
      });

      // Verify error state
      expect(result.current.errors.checkout).toBe(errorMessage);
      expect(result.current.loading.creatingCheckout).toBe(false);

      // Verify no redirect occurred
      expect(mockLocation.href).toBe('');
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.createCheckoutSession('price_test_123');
      });

      // Verify error state
      expect(result.current.errors.checkout).toBe('Network error');
      expect(result.current.loading.creatingCheckout).toBe(false);
    });

    it('should handle missing URL in response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessionId: 'cs_test_123' }), // Missing url
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.createCheckoutSession('price_test_123');
      });

      // Verify error state
      expect(result.current.errors.checkout).toBe('No checkout URL received from server');
      expect(result.current.loading.creatingCheckout).toBe(false);
    });

    it('should set loading state during request', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockReturnValueOnce(promise);

      const { result } = renderHook(() => useSubscription());

      // Start the request
      act(() => {
        result.current.createCheckoutSession('price_test_123');
      });

      // Verify loading state is true
      expect(result.current.loading.creatingCheckout).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({ url: 'https://checkout.stripe.com/pay/cs_test_123' }),
        });
      });

      // Verify loading state is false
      expect(result.current.loading.creatingCheckout).toBe(false);
    });
  });

  describe('openCustomerPortal', () => {
    it('should open customer portal and redirect on success', async () => {
      const mockResponse = {
        url: 'https://billing.stripe.com/session/bps_test_123',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.openCustomerPortal();
      });

      // Verify API call
      expect(mockFetch).toHaveBeenCalledWith('/api/stripe/create-portal-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      // Verify redirect
      expect(mockLocation.href).toBe('https://billing.stripe.com/session/bps_test_123');

      // Verify no errors
      expect(result.current.errors.portal).toBeNull();
      expect(result.current.loading.openingPortal).toBe(false);
    });

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'No active subscription found';
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: errorMessage }),
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.openCustomerPortal();
      });

      // Verify error state
      expect(result.current.errors.portal).toBe(errorMessage);
      expect(result.current.loading.openingPortal).toBe(false);

      // Verify no redirect occurred
      expect(mockLocation.href).toBe('');
    });

    it('should handle missing URL in response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}), // Missing url
      });

      const { result } = renderHook(() => useSubscription());

      await act(async () => {
        await result.current.openCustomerPortal();
      });

      // Verify error state
      expect(result.current.errors.portal).toBe('No portal URL received from server');
      expect(result.current.loading.openingPortal).toBe(false);
    });

    it('should set loading state during request', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockReturnValueOnce(promise);

      const { result } = renderHook(() => useSubscription());

      // Start the request
      act(() => {
        result.current.openCustomerPortal();
      });

      // Verify loading state is true
      expect(result.current.loading.openingPortal).toBe(true);

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({ url: 'https://billing.stripe.com/session/bps_test_123' }),
        });
      });

      // Verify loading state is false
      expect(result.current.loading.openingPortal).toBe(false);
    });
  });

  describe('clearError', () => {
    it('should clear specific error types', async () => {
      // Set up errors
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Checkout error' }),
      });

      const { result } = renderHook(() => useSubscription());

      // Create an error
      await act(async () => {
        await result.current.createCheckoutSession('invalid_price');
      });

      expect(result.current.errors.checkout).toBe('Checkout error');

      // Clear the error
      act(() => {
        result.current.clearError('checkout');
      });

      expect(result.current.errors.checkout).toBeNull();
    });

    it('should only clear the specified error type', async () => {
      const { result } = renderHook(() => useSubscription());

      // Manually set multiple errors for testing
      act(() => {
        result.current.clearError('checkout'); // This will initialize the state
      });

      // Set errors by calling functions that fail
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Checkout error' }),
      });

      await act(async () => {
        await result.current.createCheckoutSession('invalid_price');
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Portal error' }),
      });

      await act(async () => {
        await result.current.openCustomerPortal();
      });

      expect(result.current.errors.checkout).toBe('Checkout error');
      expect(result.current.errors.portal).toBe('Portal error');

      // Clear only checkout error
      act(() => {
        result.current.clearError('checkout');
      });

      expect(result.current.errors.checkout).toBeNull();
      expect(result.current.errors.portal).toBe('Portal error');
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useSubscription());

      expect(result.current.loading).toEqual({
        creatingCheckout: false,
        openingPortal: false,
        refreshingUser: false,
      });

      expect(result.current.errors).toEqual({
        checkout: null,
        portal: null,
        user: null,
      });

      expect(typeof result.current.createCheckoutSession).toBe('function');
      expect(typeof result.current.openCustomerPortal).toBe('function');
      expect(typeof result.current.clearError).toBe('function');
    });
  });
});