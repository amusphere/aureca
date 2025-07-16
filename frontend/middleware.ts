import { NextFetchEvent, NextRequest, NextResponse } from 'next/server';
import { User } from './types/User';

// Configuration
const AUTH_SYSTEM = process.env.NEXT_PUBLIC_AUTH_SYSTEM;
const LOGIN_URL = '/';

// Initialize Clerk middleware if needed
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let clerkMiddleware: any = null;
if (AUTH_SYSTEM === 'clerk') {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { clerkMiddleware: clerk } = require('@clerk/nextjs/server');
    clerkMiddleware = clerk;
  } catch {
    console.warn('Clerk middleware not available');
  }
}

/**
 * Helper functions
 */

/**
 * Check if user is authenticated (email_password only)
 */
async function isEmailPasswordAuthenticated(request: NextRequest): Promise<boolean> {
  const accessToken = request.cookies.get('access_token');
  const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:8000/api';
  const res = await fetch(`${apiBaseUrl}/users/me`, {
    headers: { 'Authorization': `Bearer ${accessToken?.value}` }
  })
  const user = await res.json() as User;
  return !!accessToken?.value && user && user.uuid ? true : false;
}

export default async function middleware(request: NextRequest, event: NextFetchEvent) {
  const { pathname } = request.nextUrl;

  if (pathname === LOGIN_URL) {
    return NextResponse.next();
  }

  // Handle Clerk authentication
  if (AUTH_SYSTEM === 'clerk' && clerkMiddleware) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return clerkMiddleware((auth: any) => {
      const { userId } = auth();
      const isUserAuthenticated = !!userId;

      if (isUserAuthenticated) {
        return NextResponse.next();
      }

      return NextResponse.redirect(new URL(LOGIN_URL, request.url));
    })(request, event);
  }

  // Handle email_password authentication
  if (AUTH_SYSTEM === 'email_password') {
    const isUserAuthenticated = await isEmailPasswordAuthenticated(request);
    if (isUserAuthenticated) {
      return NextResponse.next();
    }
  }

  return NextResponse.redirect(new URL(LOGIN_URL, request.url));
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - auth/ (authentication pages)
     * - root path (/)
     * - files with extensions (static files)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|auth/|^/$|.*\\.[a-z]+$).*)',
  ],
}