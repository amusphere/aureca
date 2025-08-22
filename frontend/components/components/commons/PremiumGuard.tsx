"use client";

import { useUser } from "@/components/hooks/useUser";
import { PremiumGuardProps } from "@/types/stripe-ui";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Crown, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { LoadingSpinner } from "./LoadingSpinner";

/**
 * PremiumGuard component that replaces Clerk's <Protect> component
 * Controls access to premium features based on subscription status
 */
export function PremiumGuard({
  children,
  fallback,
  showUpgrade = true,
  upgradeMessage = "この機能を利用するには有料プランへのアップグレードが必要です。"
}: PremiumGuardProps) {
  const { user, isLoading, isPremium } = useUser();
  const router = useRouter();

  // Show loading state while fetching user data
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner size="sm" />
      </div>
    );
  }

  // If user is not authenticated, don't show premium content
  if (!user) {
    return null;
  }

  // If user has premium access, show the protected content
  if (isPremium) {
    return <>{children}</>;
  }

  // If custom fallback is provided, use it
  if (fallback) {
    return <>{fallback}</>;
  }

  // If showUpgrade is false, don't show anything
  if (!showUpgrade) {
    return null;
  }

  // Default upgrade prompt
  const handleUpgrade = () => {
    router.push("/subscription");
  };

  return (
    <Card className="border-2 border-dashed border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50">
      <CardHeader className="text-center pb-4">
        <div className="flex justify-center mb-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
            <Crown className="h-6 w-6 text-amber-600" />
          </div>
        </div>
        <CardTitle className="text-lg font-semibold text-amber-900">
          プレミアム機能
        </CardTitle>
        <CardDescription className="text-amber-700">
          {upgradeMessage}
        </CardDescription>
      </CardHeader>
      <CardContent className="text-center">
        <Button onClick={handleUpgrade} className="bg-amber-600 hover:bg-amber-700">
          <Sparkles className="mr-2 h-4 w-4" />
          有料プランにアップグレード
        </Button>
      </CardContent>
    </Card>
  );
}

/**
 * Utility component for inline premium feature protection
 * Shows a simple upgrade button instead of a full card
 */
export function InlinePremiumGuard({
  children,
  fallback,
  showUpgrade = true,
  upgradeMessage = "プレミアム機能"
}: PremiumGuardProps) {
  const { user, isLoading, isPremium } = useUser();
  const router = useRouter();

  // Show loading state while fetching user data
  if (isLoading) {
    return (
      <div className="inline-flex items-center">
        <LoadingSpinner size="xs" />
      </div>
    );
  }

  // If user is not authenticated, don't show premium content
  if (!user) {
    return null;
  }

  // If user has premium access, show the protected content
  if (isPremium) {
    return <>{children}</>;
  }

  // If custom fallback is provided, use it
  if (fallback) {
    return <>{fallback}</>;
  }

  // If showUpgrade is false, don't show anything
  if (!showUpgrade) {
    return null;
  }

  // Inline upgrade button
  const handleUpgrade = () => {
    router.push("/subscription");
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleUpgrade}
      className="border-amber-200 text-amber-700 hover:bg-amber-50"
    >
      <Crown className="mr-1 h-3 w-3" />
      {upgradeMessage}
    </Button>
  );
}