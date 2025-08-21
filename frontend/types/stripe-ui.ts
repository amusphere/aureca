/**
 * UI-specific types for Stripe integration components
 */

import { SubscriptionStatus, UserSubscription } from './Subscription';

/**
 * Props for PremiumGuard component
 */
export interface PremiumGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgrade?: boolean;
  upgradeMessage?: string;
}

/**
 * Props for subscription status display components
 */
export interface SubscriptionStatusProps {
  subscription: UserSubscription | null;
  showDetails?: boolean;
  className?: string;
}

/**
 * Props for upgrade prompt components
 */
export interface UpgradePromptProps {
  message?: string;
  buttonText?: string;
  onUpgrade?: () => void;
  className?: string;
}

/**
 * Subscription plan information for UI display
 */
export interface PlanInfo {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
  popular?: boolean;
  stripePriceId: string;
}

/**
 * Loading states for subscription operations
 */
export interface SubscriptionLoadingStates {
  creatingCheckout: boolean;
  openingPortal: boolean;
  refreshingUser: boolean;
}

/**
 * Error states for subscription operations
 */
export interface SubscriptionErrorStates {
  checkout: string | null;
  portal: string | null;
  user: string | null;
}

/**
 * Subscription status display configuration
 */
export type StatusDisplayConfig = {
  [K in SubscriptionStatus]: {
    label: string;
    color: 'success' | 'warning' | 'error' | 'info';
    description: string;
  };
};

/**
 * Hook return type for subscription management
 */
export interface UseSubscriptionReturn {
  createCheckoutSession: (priceId: string) => Promise<void>;
  openCustomerPortal: () => Promise<void>;
  loading: SubscriptionLoadingStates;
  errors: SubscriptionErrorStates;
  clearError: (type: keyof SubscriptionErrorStates) => void;
}

/**
 * Hook return type for user with subscription
 */
export interface UseUserReturn {
  user: import('./User').UserWithSubscription | null;
  isLoading: boolean;
  error: string | null;
  isPremium: boolean;
  refreshUser: () => Promise<void>;
}