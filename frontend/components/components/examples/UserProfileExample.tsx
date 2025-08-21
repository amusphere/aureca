"use client";

import { useUser } from '@/components/hooks/useUser';
import { Button } from '@/components/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/components/ui/card';
import { Badge } from '@/components/components/ui/badge';
import { Loader2, RefreshCw, User, Crown } from 'lucide-react';

/**
 * Example component demonstrating useUser hook usage
 * Shows user information, subscription status, and refresh functionality
 */
export function UserProfileExample() {
  const { user, isLoading, error, isPremium, refreshUser } = useUser();

  if (isLoading) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading user data...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">Error: {error}</p>
            <Button onClick={refreshUser} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!user) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <div className="text-center">
            <User className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">No user data available</p>
            <Button onClick={refreshUser} variant="outline" className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <User className="h-5 w-5 mr-2" />
            User Profile
          </CardTitle>
          <Button onClick={refreshUser} variant="ghost" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          Current user information and subscription status
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* User Basic Info */}
        <div>
          <h3 className="font-medium mb-2">Basic Information</h3>
          <div className="space-y-1 text-sm">
            <p><span className="font-medium">Name:</span> {user.name || 'Not provided'}</p>
            <p><span className="font-medium">Email:</span> {user.email || 'Not provided'}</p>
            <p><span className="font-medium">User ID:</span> {user.uuid}</p>
          </div>
        </div>

        {/* Subscription Status */}
        <div>
          <h3 className="font-medium mb-2 flex items-center">
            Subscription Status
            {isPremium && <Crown className="h-4 w-4 ml-2 text-yellow-500" />}
          </h3>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={isPremium ? "default" : "secondary"}>
                {isPremium ? "Premium" : "Free"}
              </Badge>
              {user.subscription?.status && (
                <Badge variant="outline">
                  {user.subscription.status}
                </Badge>
              )}
            </div>

            {user.subscription && (
              <div className="text-sm space-y-1">
                {user.subscription.planName && (
                  <p><span className="font-medium">Plan:</span> {user.subscription.planName}</p>
                )}
                {user.subscription.currentPeriodEnd && (
                  <p>
                    <span className="font-medium">Expires:</span>{' '}
                    {new Date(user.subscription.currentPeriodEnd * 1000).toLocaleDateString()}
                  </p>
                )}
                {user.subscription.cancelAtPeriodEnd && (
                  <p className="text-orange-600">
                    ⚠️ Subscription will cancel at period end
                  </p>
                )}
              </div>
            )}

            {!user.subscription && (
              <p className="text-sm text-gray-600">
                No active subscription
              </p>
            )}
          </div>
        </div>

        {/* Stripe Customer Info */}
        {user.stripeCustomerId && (
          <div>
            <h3 className="font-medium mb-2">Billing Information</h3>
            <p className="text-sm">
              <span className="font-medium">Stripe Customer:</span>{' '}
              <code className="text-xs bg-gray-100 px-1 rounded">
                {user.stripeCustomerId}
              </code>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}