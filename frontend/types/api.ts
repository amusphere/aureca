/**
 * API-specific type definitions for request/response payloads
 */

import { CheckoutSessionRequest, CheckoutSessionResponse, CustomerPortalResponse } from './Subscription';

/**
 * Stripe API endpoint types
 */
export interface StripeApiEndpoints {
  '/api/stripe/create-checkout-session': {
    request: CheckoutSessionRequest;
    response: CheckoutSessionResponse;
  };
  '/api/stripe/create-portal-session': {
    request: never; // No request body needed
    response: CustomerPortalResponse;
  };
}

/**
 * User API endpoint types
 */
export interface UserApiEndpoints {
  '/api/users/me': {
    request: never; // GET request, no body
    response: import('./User').UserWithSubscription;
  };
}

/**
 * Combined API endpoint types for type-safe API calls
 */
export type ApiEndpoints = StripeApiEndpoints & UserApiEndpoints;

/**
 * Extract request type for a given endpoint
 */
export type ApiRequest<T extends keyof ApiEndpoints> = ApiEndpoints[T]['request'];

/**
 * Extract response type for a given endpoint
 */
export type ApiResponseData<T extends keyof ApiEndpoints> = ApiEndpoints[T]['response'];