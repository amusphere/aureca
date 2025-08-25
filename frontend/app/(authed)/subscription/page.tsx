"use client";

import { Alert, AlertDescription } from '@/components/components/ui/alert';
import { Badge } from '@/components/components/ui/badge';
import { Button } from '@/components/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/components/ui/card';
import { Separator } from '@/components/components/ui/separator';
import { Skeleton } from '@/components/components/ui/skeleton';
import { useSubscription } from '@/components/hooks/useSubscription';
import { useUser } from '@/components/hooks/useUser';
import React, { useEffect, useState } from 'react';

// Stripe Pricing Table component type declaration
interface StripePricingTableProps {
  'pricing-table-id': string;
  'publishable-key': string;
  'customer-email'?: string;
  'client-reference-id'?: string;
}

export default function SubscriptionPage() {
  const { user, isLoading: userLoading, isPremium, refreshUser } = useUser();
  const { openCustomerPortal, loading, errors, clearError } = useSubscription();
  const [stripeLoaded, setStripeLoaded] = useState(false);

  // Load Stripe Pricing Table script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/pricing-table.js';
    script.async = true;
    script.onload = () => setStripeLoaded(true);
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  // Handle success/cancel URL parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const canceled = urlParams.get('canceled');

    if (success === 'true') {
      // Refresh user data after successful payment
      refreshUser();
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (canceled === 'true') {
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [refreshUser]);

  const handleOpenPortal = async () => {
    clearError('portal');
    await openCustomerPortal();
  };

  const formatDate = (timestamp: number | null) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusBadgeVariant = (status: string | null) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'trialing':
        return 'secondary';
      case 'canceled':
      case 'past_due':
      case 'unpaid':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusLabel = (status: string | null) => {
    switch (status) {
      case 'active':
        return 'アクティブ';
      case 'trialing':
        return 'トライアル中';
      case 'canceled':
        return 'キャンセル済み';
      case 'past_due':
        return '支払い遅延';
      case 'unpaid':
        return '未払い';
      case 'incomplete':
        return '不完全';
      case 'incomplete_expired':
        return '期限切れ';
      default:
        return '不明';
    }
  };

  if (userLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-10 w-32" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">サブスクリプション管理</h1>
          <p className="text-muted-foreground">
            プランの管理と請求情報の確認ができます
          </p>
        </div>

        {/* Current Plan Status */}
        {user && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>現在のプラン</span>
                {user.subscription?.status && (
                  <Badge variant={getStatusBadgeVariant(user.subscription.status)}>
                    {getStatusLabel(user.subscription.status)}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                あなたの現在のサブスクリプション状況
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isPremium && user.subscription ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">プラン名</p>
                      <p className="text-lg font-semibold">
                        {user.subscription.planName || 'Premium'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">次回更新日</p>
                      <p className="text-lg">
                        {formatDate(user.subscription.currentPeriodEnd)}
                      </p>
                    </div>
                  </div>

                  {user.subscription.cancelAtPeriodEnd && (
                    <Alert>
                      <AlertDescription>
                        このサブスクリプションは{formatDate(user.subscription.currentPeriodEnd)}にキャンセルされます。
                        それまでは引き続きプレミアム機能をご利用いただけます。
                      </AlertDescription>
                    </Alert>
                  )}

                  <Separator />

                  <div className="flex flex-col sm:flex-row gap-3">
                    <Button
                      onClick={handleOpenPortal}
                      disabled={loading.openingPortal}
                      className="flex-1 sm:flex-none"
                    >
                      {loading.openingPortal ? '読み込み中...' : '請求情報を管理'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={refreshUser}
                      disabled={loading.refreshingUser}
                      className="flex-1 sm:flex-none"
                    >
                      {loading.refreshingUser ? '更新中...' : '状況を更新'}
                    </Button>
                  </div>

                  {errors.portal && (
                    <Alert variant="destructive">
                      <AlertDescription>{errors.portal.message}</AlertDescription>
                    </Alert>
                  )}
                </div>
              ) : (
                <div className="text-center space-y-4">
                  <div className="space-y-2">
                    <p className="text-lg font-medium">フリープラン</p>
                    <p className="text-muted-foreground">
                      現在フリープランをご利用中です。プレミアム機能をご利用になるには、下記からプランをお選びください。
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Pricing Table */}
        {!isPremium && (
          <Card>
            <CardHeader>
              <CardTitle>プランを選択</CardTitle>
              <CardDescription>
                あなたに最適なプランをお選びください
              </CardDescription>
            </CardHeader>
            <CardContent>
              {stripeLoaded && process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY && process.env.NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID ? (
                <div className="w-full">
                  {React.createElement('stripe-pricing-table', {
                    'pricing-table-id': process.env.NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID,
                    'publishable-key': process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
                    'customer-email': user?.email || undefined,
                    'client-reference-id': user?.uuid || undefined,
                  } as StripePricingTableProps)}
                </div>
              ) : (
                <div className="text-center py-8">
                  {!stripeLoaded ? (
                    <div className="space-y-3">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                      <p className="text-muted-foreground">料金表を読み込み中...</p>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">
                      {!process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
                        ? 'Stripe Publishable Keyが設定されていません'
                        : !process.env.NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID
                          ? 'Stripe Pricing Table IDが設定されていません'
                          : 'Stripe設定が必要です'
                      }
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Help Section */}
        <Card>
          <CardHeader>
            <CardTitle>サポート</CardTitle>
            <CardDescription>
              ご質問やお困りのことがございましたら
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">よくある質問</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• プランの変更方法</li>
                    <li>• 請求書の確認方法</li>
                    <li>• キャンセル手続き</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">お問い合わせ</h4>
                  <p className="text-sm text-muted-foreground">
                    技術的なサポートが必要な場合は、
                    <br />
                    サポートチームまでご連絡ください。
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
