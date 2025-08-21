# React Hooks for Stripe Billing Integration

This directory contains custom React hooks for managing user data and Stripe subscription operations.

## Available Hooks

- [`useUser`](#useuser-hook) - User data management with subscription information
- [`useSubscription`](#usesubscription-hook) - Stripe subscription operations

---

# useUser Hook

The `useUser` hook provides comprehensive user management with subscription information, caching, and refresh capabilities for the Stripe billing integration.

## Features

- **User Data Fetching**: Automatically fetches user data with subscription information
- **Premium Status**: Provides `isPremium` boolean for easy access control
- **Caching**: Caches user data to minimize API calls
- **Refresh Capability**: Manual refresh function for updating subscription status
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Loading States**: Proper loading state management

## Usage

```typescript
import { useUser } from '@/components/hooks/useUser';

function MyComponent() {
  const { user, isLoading, error, isPremium, refreshUser } = useUser();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Welcome, {user?.name || 'User'}!</h1>
      {isPremium ? (
        <p>You have premium access!</p>
      ) : (
        <p>Upgrade to premium for more features</p>
      )}
      <button onClick={refreshUser}>Refresh User Data</button>
    </div>
  );
}
```

## Return Values

| Property | Type | Description |
|----------|------|-------------|
| `user` | `UserWithSubscription \| null` | Complete user object with subscription info |
| `isLoading` | `boolean` | Loading state for initial fetch and refresh |
| `error` | `string \| null` | Error message if fetch fails |
| `isPremium` | `boolean` | Computed premium status from subscription |
| `refreshUser` | `() => Promise<void>` | Function to manually refresh user data |

## User Object Structure

```typescript
interface UserWithSubscription {
  id: number;
  uuid: string;
  email: string | null;
  name: string | null;
  clerkSub: string | null;
  stripeCustomerId: string | null;
  createdAt: number;
  subscription: {
    isPremium: boolean;
    planName: string | null;
    status: SubscriptionStatus | null;
    currentPeriodEnd: number | null;
    cancelAtPeriodEnd: boolean;
    stripeSubscriptionId: string | null;
    stripePriceId: string | null;
  } | null;
}
```

## Premium Status Logic

The `isPremium` property is determined by:
- `user?.subscription?.isPremium ?? false`

This ensures that:
- Users without subscriptions are not premium
- Users with inactive subscriptions are not premium
- Only users with active, valid subscriptions are premium

## Error Handling

The hook handles various error scenarios:

- **401 Unauthorized**: Sets user to null without error (user not authenticated)
- **API Errors**: Shows error message with details from server
- **Network Errors**: Shows network error message
- **JSON Parse Errors**: Handles malformed responses gracefully

## Caching Behavior

- Data is cached in component state after initial fetch
- Manual refresh updates the cache
- No automatic refresh intervals (call `refreshUser` when needed)
- Cache is cleared when component unmounts

## Integration with Stripe

This hook is designed to work with the Stripe billing migration:

1. Fetches user data from `/api/users/me` endpoint
2. Includes subscription information from Stripe
3. Provides premium status for feature gating
4. Supports refresh after subscription changes

## Common Use Cases

### Feature Gating
```typescript
const { isPremium } = useUser();

return (
  <div>
    {isPremium ? (
      <PremiumFeature />
    ) : (
      <UpgradePrompt />
    )}
  </div>
);
```

### Subscription Status Display
```typescript
const { user } = useUser();

return (
  <div>
    <p>Plan: {user?.subscription?.planName || 'Free'}</p>
    <p>Status: {user?.subscription?.status || 'None'}</p>
  </div>
);
```

### Refresh After Subscription Changes
```typescript
const { refreshUser } = useUser();

const handleSubscriptionSuccess = async () => {
  // After successful Stripe checkout
  await refreshUser();
  // User data now includes new subscription
};
```

## Testing

The hook includes comprehensive tests:
- Unit tests for all functionality
- Integration tests with mocked API calls
- Error scenario testing
- Subscription status change testing

Run tests with:
```bash
npm test -- useUser.test.ts --run
npm test -- useUser.integration.test.ts --run
```

---

# useSubscription Hook

The `useSubscription` hook provides Stripe subscription management functionality, including checkout session creation and customer portal access.

## Features

- **Checkout Session Creation**: Create Stripe checkout sessions for subscription purchases
- **Customer Portal Access**: Open Stripe customer portal for subscription management
- **Loading States**: Granular loading states for different operations
- **Error Handling**: Comprehensive error handling with specific error types
- **URL Redirection**: Automatic redirection to Stripe hosted pages

## Usage

```typescript
import { useSubscription } from '@/components/hooks/useSubscription';

function SubscriptionComponent() {
  const {
    createCheckoutSession,
    openCustomerPortal,
    loading,
    errors,
    clearError
  } = useSubscription();

  const handleUpgrade = async () => {
    await createCheckoutSession('price_1234567890');
  };

  const handleManageSubscription = async () => {
    await openCustomerPortal();
  };

  return (
    <div>
      {errors.checkout && (
        <div className="error">
          {errors.checkout}
          <button onClick={() => clearError('checkout')}>Dismiss</button>
        </div>
      )}

      <button
        onClick={handleUpgrade}
        disabled={loading.creatingCheckout}
      >
        {loading.creatingCheckout ? 'Creating...' : 'Upgrade to Premium'}
      </button>

      <button
        onClick={handleManageSubscription}
        disabled={loading.openingPortal}
      >
        {loading.openingPortal ? 'Opening...' : 'Manage Subscription'}
      </button>
    </div>
  );
}
```

## Return Values

| Property | Type | Description |
|----------|------|-------------|
| `createCheckoutSession` | `(priceId: string) => Promise<void>` | Creates checkout session and redirects to Stripe |
| `openCustomerPortal` | `() => Promise<void>` | Opens customer portal and redirects to Stripe |
| `loading` | `SubscriptionLoadingStates` | Loading states for different operations |
| `errors` | `SubscriptionErrorStates` | Error states for different operations |
| `clearError` | `(type: keyof SubscriptionErrorStates) => void` | Clear specific error types |

## Loading States

```typescript
interface SubscriptionLoadingStates {
  creatingCheckout: boolean;  // True when creating checkout session
  openingPortal: boolean;     // True when opening customer portal
  refreshingUser: boolean;    // Reserved for future user refresh integration
}
```

## Error States

```typescript
interface SubscriptionErrorStates {
  checkout: string | null;    // Checkout session creation errors
  portal: string | null;      // Customer portal access errors
  user: string | null;        // Reserved for future user-related errors
}
```

## API Integration

### Checkout Session Creation

The hook calls `/api/stripe/create-checkout-session` with:

```typescript
interface CheckoutSessionRequest {
  priceId: string;
  successUrl?: string;  // Defaults to /subscription?success=true
  cancelUrl?: string;   // Defaults to /subscription?canceled=true
}
```

### Customer Portal Access

The hook calls `/api/stripe/create-portal-session` with no request body.

## URL Handling

The hook automatically constructs success and cancel URLs:
- **Success URL**: `${window.location.origin}/subscription?success=true`
- **Cancel URL**: `${window.location.origin}/subscription?canceled=true`

These can be customized by modifying the hook implementation.

## Error Handling

The hook handles various error scenarios:

- **API Errors**: Server-side validation or Stripe API errors
- **Network Errors**: Connection failures or timeouts
- **Missing URLs**: Server doesn't return expected redirect URLs
- **Authentication Errors**: User not authenticated for protected endpoints

## Common Use Cases

### Basic Subscription Upgrade
```typescript
const { createCheckoutSession, loading, errors } = useSubscription();

const handleUpgrade = async () => {
  await createCheckoutSession('price_monthly_plan');
  // User will be redirected to Stripe Checkout
};
```

### Subscription Management
```typescript
const { openCustomerPortal, loading } = useSubscription();

const handleManageSubscription = async () => {
  await openCustomerPortal();
  // User will be redirected to Stripe Customer Portal
};
```

### Error Handling with User Feedback
```typescript
const { createCheckoutSession, errors, clearError } = useSubscription();

return (
  <div>
    {errors.checkout && (
      <Alert variant="destructive">
        <AlertDescription>
          {errors.checkout}
          <Button onClick={() => clearError('checkout')}>
            Dismiss
          </Button>
        </AlertDescription>
      </Alert>
    )}
    {/* Rest of component */}
  </div>
);
```

### Loading States with UI Feedback
```typescript
const { createCheckoutSession, loading } = useSubscription();

return (
  <Button
    onClick={() => createCheckoutSession('price_123')}
    disabled={loading.creatingCheckout}
  >
    {loading.creatingCheckout ? (
      <>
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Creating...
      </>
    ) : (
      'Upgrade Now'
    )}
  </Button>
);
```

## Integration with useUser

The hooks work together for complete subscription management:

```typescript
const { user, isPremium, refreshUser } = useUser();
const { createCheckoutSession, openCustomerPortal } = useSubscription();

// Show different UI based on subscription status
if (!isPremium) {
  return <UpgradeButton onClick={() => createCheckoutSession('price_123')} />;
} else {
  return <ManageButton onClick={openCustomerPortal} />;
}
```

## Testing

The hook includes comprehensive tests covering:
- Successful checkout session creation
- Successful customer portal access
- API error handling
- Network error handling
- Loading state management
- Error clearing functionality

Run tests with:
```bash
npm test -- useSubscription.test.ts --run
```

## Example Component

See `frontend/components/components/examples/SubscriptionExample.tsx` for a complete example demonstrating all hook features.