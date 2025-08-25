import { SubscriptionInfo, UserSubscription } from './Subscription';

/**
 * Base user information
 */
export interface User {
  id: number;
  uuid: string;
  email: string | null;
  name: string | null;
  clerkSub: string | null;
  stripeCustomerId: string | null;
  createdAt: number;
}

/**
 * User information with subscription details from Stripe API
 * This matches the response from /api/users/me endpoint after Stripe migration
 */
export interface UserWithSubscription extends User {
  subscription: SubscriptionInfo | null;
}

/**
 * Legacy user with subscription interface
 * @deprecated Use UserWithSubscription instead
 */
export interface LegacyUserWithSubscription extends User {
  subscription: UserSubscription | null;
}
