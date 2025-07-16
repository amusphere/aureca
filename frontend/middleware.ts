import { NextFetchEvent, NextRequest, NextResponse } from 'next/server';

// Configuration
const AUTH_SYSTEM = process.env.NEXT_PUBLIC_AUTH_SYSTEM;
const LOGIN_URL = '/';
const AUTHENTICATED_REDIRECT_URL = '/home';

// Routes that don't require authentication (all others require authentication)
const PUBLIC_ROUTES = ['/'];

// Routes to skip middleware entirely
const SKIP_ROUTES = [
  '/_next',
  '/api',
  '/auth/',
  // Static files
  /\.(html?|css|js|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)$/
];

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
 * Check if the route should skip middleware entirely
 */
function shouldSkipMiddleware(pathname: string): boolean {
  return SKIP_ROUTES.some(skipRoute => {
    if (typeof skipRoute === 'string') {
      return pathname.startsWith(skipRoute);
    }
    if (skipRoute instanceof RegExp) {
      return skipRoute.test(pathname);
    }
    return false;
  });
}

/**
 * Check if user is authenticated (email_password only)
 */
function isEmailPasswordAuthenticated(request: NextRequest): boolean {
  const accessToken = request.cookies.get('access_token');
  return !!accessToken?.value;
}

/**
 * Check if the route is public (doesn't require authentication)
 */
function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.includes(pathname);
}

/**
 * Handle authentication logic for both auth systems
 */
function handleAuthentication(
  pathname: string,
  isAuthenticated: boolean,
  request: NextRequest
): NextResponse | null {
  const isPublic = isPublicRoute(pathname);

  // If accessing public route while authenticated, redirect to home
  if (isPublic && isAuthenticated) {
    return NextResponse.redirect(new URL(AUTHENTICATED_REDIRECT_URL, request.url));
  }

  // If accessing protected route while not authenticated, redirect to login
  if (!isPublic && !isAuthenticated) {
    return NextResponse.redirect(new URL(LOGIN_URL, request.url));
  }

  // Allow access
  return null;
}

export default async function middleware(request: NextRequest, event: NextFetchEvent) {
  const { pathname } = request.nextUrl;

  // Skip middleware for certain routes
  if (shouldSkipMiddleware(pathname)) {
    return NextResponse.next();
  }

  // Handle Clerk authentication
  if (AUTH_SYSTEM === 'clerk' && clerkMiddleware) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return clerkMiddleware((auth: any) => {
      const { userId } = auth();
      const isUserAuthenticated = !!userId;

      return handleAuthentication(pathname, isUserAuthenticated, request);
    })(request, event);
  }

  // Handle email_password authentication
  if (AUTH_SYSTEM === 'email_password') {
    const isUserAuthenticated = isEmailPasswordAuthenticated(request);
    return handleAuthentication(pathname, isUserAuthenticated, request);
  }

  // Fallback: treat all routes as protected if auth system is not configured
  if (!isPublicRoute(pathname)) {
    return NextResponse.redirect(new URL(LOGIN_URL, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}