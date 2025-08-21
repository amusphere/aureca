import { UserSubscription } from './Subscription';

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
 * User information with subscription details
 * This matches the response from /api/users/me endpoint
 */
export interface UserWithSubscription extends User {
  subscription: UserSubscription | null;
}
