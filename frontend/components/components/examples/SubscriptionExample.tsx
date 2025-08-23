"use client";

import React from 'react';
import { useUser } from '@/components/hooks/useUser';
import { useSubscription } from '@/components/hooks/useSubscription';
import { Button } from '@/components/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/components/ui/card';
import { Badge } from '@/components/components/ui/badge';
import { Crown, Settings } from 'lucide-react';

/**
 * Example component demonstrating subscription management
 * This shows how to integrate Stripe checkout and customer portal
 */
export function SubscriptionExample() {
  const { user, isLoading, isPremium } = useUser();
  const { createCheckoutSession, openCustomerPortal, loading, errors } = useSubscription();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <div>Please log in to view subscription information.</div>;
  }

  const handleUpgrade = async () => {
    // Replace with actual price ID from Stripe
    await createCheckoutSession('price_1234567890');
  };

  const handleManageSubscription = async () => {
    await openCustomerPortal();
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">Subscription Management</h2>
        <p className="text-muted-foreground">
          Manage your subscription and billing information
        </p>
      </div>

      {/* Current Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-5 w-5" />
            Current Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={isPremium ? "default" : "secondary"}>
                  {user.subscription?.planName || "Free"}
                </Badge>
                {user.subscription?.status && (
                  <Badge variant="outline">
                    {user.subscription.status}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                {isPremium
                  ? "You have access to all premium features"
                  : "Upgrade to unlock premium features"
                }
              </p>
              {user.subscription?.currentPeriodEnd && (
                <p className="text-xs text-muted-foreground mt-1">
                  {user.subscription.cancelAtPeriodEnd
                    ? "Cancels on "
                    : "Renews on "
                  }
                  {new Date(user.subscription.currentPeriodEnd * 1000).toLocaleDateString()}
                </p>
              )}
            </div>

            <div className="flex gap-2">
              {!isPremium ? (
                <Button
                  onClick={handleUpgrade}
                  disabled={loading.creatingCheckout}
                >
                  <Crown className="mr-2 h-4 w-4" />
                  {loading.creatingCheckout ? "Loading..." : "Upgrade"}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={handleManageSubscription}
                  disabled={loading.openingPortal}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  {loading.openingPortal ? "Loading..." : "Manage"}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {(errors.checkout || errors.portal || errors.user) && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-700">
              {errors.checkout?.message || errors.portal?.message || errors.user?.message}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Feature Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Feature Comparison</CardTitle>
          <CardDescription>
            See what&apos;s included in each plan
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold">Free Plan</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full" />
                  Basic task management
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full" />
                  Manual task creation
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full" />
                  Limited storage
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Crown className="h-4 w-4 text-amber-600" />
                Premium Plan
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  AI-powered task generation
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  Smart scheduling suggestions
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  Email integration
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  Calendar sync
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  Unlimited storage
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}