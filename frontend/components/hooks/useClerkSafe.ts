"use client";

import { useClerk } from "@clerk/nextjs";

/**
 * A safe wrapper around useClerk that handles cases where ClerkProvider is not available
 */
export function useClerkSafe() {
  try {
    const clerk = useClerk();
    return clerk;
  } catch (error) {
    // ClerkProvider is not available
    if (process.env.NODE_ENV === 'development') {
      console.warn("ClerkProvider not available:", error);
    }
    return null;
  }
}