"use client";

import { useEffect, useState } from "react";
import { useClerkSafe } from "@/components/hooks/useClerkSafe";

// Force dynamic rendering to avoid prerendering during build
export const dynamic = 'force-dynamic';

export default function SignOutPage() {
  const clerk = useClerkSafe();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const performSignOut = async () => {
      try {
        setIsSigningOut(true);
        
        if (clerk && clerk.signOut) {
          // Use Clerk signOut if available
          await clerk.signOut();
          return;
        }

        // Fallback: redirect to home page
        console.log("Clerk not available, using fallback signout - redirecting to home");
        window.location.href = "/";
        
      } catch (error) {
        console.error("Sign out error:", error);
        setError("Failed to sign out. Redirecting to home...");
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      }
    };

    performSignOut();
  }, [clerk]);

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
