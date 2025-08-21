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