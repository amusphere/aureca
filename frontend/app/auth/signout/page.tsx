"use client";

import { useEffect, useState } from "react";

// Force dynamic rendering to avoid prerendering during build
export const dynamic = 'force-dynamic';

export default function SignOutPage() {
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const performSignOut = async () => {
      try {
        setIsSigningOut(true);

        // Check auth system type
        const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

        if (authSystem === 'clerk') {
          // Try to use Clerk signout
          try {
            // Check if Clerk is available in the global scope
            const clerk = (window as { Clerk?: { signOut: () => Promise<void> } }).Clerk;
            if (clerk && clerk.signOut) {
              await clerk.signOut();
              return;
            }
          } catch (clerkError) {
            // Clerk not available - continue with fallback
          }
        } else if (authSystem === 'email_password') {
          // Use API endpoint for email/password auth
          try {
            await fetch('/api/auth/signout');
          } catch (apiError) {
            // API signout failed - continue with fallback
          }
        }

        // Fallback: redirect to home page
        window.location.href = "/";

      } catch (error) {
        setError("Failed to sign out. Redirecting to home...");
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      }
    };

    performSignOut();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-lg">Signing out...</p>
        {isSigningOut && (
          <div className="mt-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          </div>
        )}
      </div>
    </div>
  );
}
