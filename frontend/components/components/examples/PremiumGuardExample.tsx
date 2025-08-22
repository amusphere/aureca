"use client";

import { PremiumGuard, InlinePremiumGuard } from "@/components/components/commons/PremiumGuard";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Sparkles, Zap, Crown } from "lucide-react";

/**
 * Example component demonstrating PremiumGuard usage
 * This shows how to replace Clerk&apos;s &lt;Protect&gt; component with PremiumGuard
 */
export function PremiumGuardExample() {
  return (
    <div className="space-y-8 p-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">PremiumGuard Examples</h2>
        <p className="text-muted-foreground mb-6">
          Examples of how to use PremiumGuard to replace Clerk&apos;s &lt;Protect&gt; component
        </p>
      </div>

      {/* Example 1: Basic Premium Feature Protection */}
      <Card>
        <CardHeader>
          <CardTitle>Example 1: Basic Premium Feature</CardTitle>
          <CardDescription>
            Shows premium content to subscribers, upgrade prompt to free users
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PremiumGuard>
            <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Crown className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-purple-900">Premium Feature</h3>
              </div>
              <p className="text-purple-700">
                This content is only visible to premium subscribers!
              </p>
              <Button className="mt-3" size="sm">
                <Sparkles className="mr-2 h-4 w-4" />
                Use Premium Feature
              </Button>
            </div>
          </PremiumGuard>
        </CardContent>
      </Card>

      {/* Example 2: Custom Upgrade Message */}
      <Card>
        <CardHeader>
          <CardTitle>Example 2: Custom Upgrade Message</CardTitle>
          <CardDescription>
            Premium feature with custom upgrade message
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PremiumGuard upgradeMessage="AI機能を使用するには有料プランが必要です。">
            <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold text-green-900">AI Assistant</h3>
              </div>
              <p className="text-green-700">
                AI-powered task generation and smart suggestions
              </p>
            </div>
          </PremiumGuard>
        </CardContent>
      </Card>

      {/* Example 3: Custom Fallback */}
      <Card>
        <CardHeader>
          <CardTitle>Example 3: Custom Fallback</CardTitle>
          <CardDescription>
            Premium feature with custom fallback content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PremiumGuard
            fallback={
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center">
                <p className="text-gray-600 mb-3">
                  Advanced analytics are available in the premium plan
                </p>
                <Button variant="outline" size="sm">
                  Learn More
                </Button>
              </div>
            }
          >
            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <h3 className="font-semibold text-blue-900 mb-2">Advanced Analytics</h3>
              <p className="text-blue-700">
                Detailed insights and performance metrics
              </p>
            </div>
          </PremiumGuard>
        </CardContent>
      </Card>

      {/* Example 4: Inline Premium Guard */}
      <Card>
        <CardHeader>
          <CardTitle>Example 4: Inline Premium Guard</CardTitle>
          <CardDescription>
            For buttons and inline elements that need premium protection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button variant="outline">
              Regular Feature
            </Button>

            <InlinePremiumGuard upgradeMessage="プレミアム機能">
              <Button>
                <Sparkles className="mr-2 h-4 w-4" />
                Premium Feature
              </Button>
            </InlinePremiumGuard>
          </div>
        </CardContent>
      </Card>

      {/* Example 5: No Upgrade Prompt */}
      <Card>
        <CardHeader>
          <CardTitle>Example 5: Hidden Premium Feature</CardTitle>
          <CardDescription>
            Premium feature that&apos;s completely hidden from free users
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p>This section always shows:</p>
            <div className="p-3 bg-gray-50 rounded border">
              <p>Regular content visible to all users</p>
            </div>

            <PremiumGuard showUpgrade={false}>
              <div className="p-3 bg-purple-50 rounded border border-purple-200">
                <p className="text-purple-700">
                  This premium content is completely hidden from free users
                </p>
              </div>
            </PremiumGuard>
          </div>
        </CardContent>
      </Card>

      {/* Migration Guide */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="text-amber-900">Migration from Clerk Protect</CardTitle>
          <CardDescription className="text-amber-700">
            How to replace Clerk&apos;s &lt;Protect&gt; component
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold text-amber-900 mb-2">Before (Clerk):</h4>
            <pre className="bg-white p-3 rounded border text-sm overflow-x-auto">
{`<Protect condition={(has) => !has({ plan: "free" })}>
  <PremiumFeature />
</Protect>`}
            </pre>
          </div>

          <div>
            <h4 className="font-semibold text-amber-900 mb-2">After (PremiumGuard):</h4>
            <pre className="bg-white p-3 rounded border text-sm overflow-x-auto">
{`<PremiumGuard>
  <PremiumFeature />
</PremiumGuard>`}
            </pre>
          </div>

          <div className="text-sm text-amber-700">
            <p className="font-medium mb-1">Key differences:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>No need for condition functions - automatically checks subscription status</li>
              <li>Built-in upgrade prompts with customizable messages</li>
              <li>Support for custom fallback content</li>
              <li>Inline variant for buttons and small elements</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}