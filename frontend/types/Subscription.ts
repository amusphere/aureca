/**
 * Subscription-related type definitions for Stripe billing integration
 */

/**
 * Subscription status values from Stripe
 */
export type SubscriptionStatus =
  | 'active'
  | 'canceled'
  | 'incomplete'
  | 'incomplete_expired'
  | 'past_due'
  | 'trialing'
  | 'unpaid';

/**
 * Core subscription information
 */
export interface Subscription {
  id: number;
  uuid: string;
  userId: number;
  stripeSubscriptionId: string;
  stripeCustomerId: string;
  stripePriceId: string;
  planName: string;
  status: SubscriptionStatus;
  currentPeriodStart: number;
  currentPeriodEnd: number;
  cancelAtPeriodEnd: boolean;
  canceledAt: number | null;
  trialStart: number | null;
  trialEnd: number | null;
  createdAt: number;
  updatedAt: number;
}

/**
 * Simplified subscription information for user context
 */
export interface UserSubscription {
  isPremium: boolean;
  planName: string | null;
  status: SubscriptionStatus | null;
  currentPeriodEnd: number | null;
  cancelAtPeriodEnd: boolean;
  stripeSubscriptionId: string | null;
  stripePriceId: string | null;
}

/**
 * Request payload for creating a Stripe checkout session
 */
export interface CheckoutSessionRequest {
  priceId: string;
  successUrl?: string;
  cancelUrl?: string;
}

/**
 * Response from creating a Stripe checkout session
 */
export interface CheckoutSessionResponse {
  sessionId: string;
  url: string;
}

/**
 * Response from creating a Stripe customer portal session
 */
export interface CustomerPortalResponse {
  url: string;
}

/**
 * Stripe webhook event types we handle
 */
export type StripeWebhookEventType =
  | 'customer.subscription.created'
  | 'customer.subscription.updated'
  | 'customer.subscription.deleted'
  | 'invoice.payment_succeeded'
  | 'invoice.payment_failed';
