import { NextFetchEvent, NextRequest, NextResponse } from 'next/server';

// Configuration
const AUTH_SYSTEM = process.env.NEXT_PUBLIC_AUTH_SYSTEM;
const LOGIN_URL = '/';
const AUTHENTICATED_REDIRECT_URL = '/home';

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
function isEmailPasswordAuthenticated(request: NextRequest): boolean {
  const accessToken = request.cookies.get('access_token');
  return !!accessToken?.value;
}

export default async function middleware(request: NextRequest, event: NextFetchEvent) {
  const { pathname } = request.nextUrl;

  // Handle Clerk authentication
  if (AUTH_SYSTEM === 'clerk' && clerkMiddleware) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return clerkMiddleware((auth: any) => {
      const { userId } = auth();
      const isUserAuthenticated = !!userId;

      // If authenticated user tries to access login page, redirect to home
      if (pathname === LOGIN_URL && isUserAuthenticated) {
        return NextResponse.redirect(new URL(AUTHENTICATED_REDIRECT_URL, request.url));
      }

      // If unauthenticated user tries to access protected route, redirect to login
      if (pathname !== LOGIN_URL && !isUserAuthenticated) {
        return NextResponse.redirect(new URL(LOGIN_URL, request.url));
      }

      return NextResponse.next();
    })(request, event);
  }

  // Handle email_password authentication
  if (AUTH_SYSTEM === 'email_password') {
    const isUserAuthenticated = isEmailPasswordAuthenticated(request);

    // If authenticated user tries to access login page, redirect to home
    if (pathname === LOGIN_URL && isUserAuthenticated) {
      return NextResponse.redirect(new URL(AUTHENTICATED_REDIRECT_URL, request.url));
    }

    // If unauthenticated user tries to access protected route, redirect to login
    if (pathname !== LOGIN_URL && !isUserAuthenticated) {
      return NextResponse.redirect(new URL(LOGIN_URL, request.url));
    }

    return NextResponse.next();
  }

  // Fallback: treat all routes as protected if auth system is not configured
  if (pathname !== LOGIN_URL) {
    return NextResponse.redirect(new URL(LOGIN_URL, request.url));
  }

  return NextResponse.next();
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