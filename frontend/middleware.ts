import { NextFetchEvent, NextRequest, NextResponse } from 'next/server';

const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

// Protected routes that require authentication
const protectedRoutes = ['/home', '/settings', '/tasks'];

// Routes that should redirect to /home if already authenticated
const publicOnlyRoutes = ['/'];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let clerkMiddleware: any = null;
try {
  if (authSystem === 'clerk') {
    // Import Clerk only when needed, but always at the top level for detection
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { clerkMiddleware: clerk } = require('@clerk/nextjs/server');
    clerkMiddleware = clerk;
  }
} catch {
  // Clerk not available, ignore
}

/**
 * Check if user is authenticated based on auth system
 */
function isAuthenticated(request: NextRequest): boolean {
  if (authSystem === 'email_password') {
    const accessToken = request.cookies.get('access_token');
    return !!accessToken?.value;
  }

  if (authSystem === 'clerk') {
    // For Clerk, we'll let clerkMiddleware handle the auth check
    // This function is only used for email_password auth
    return true;
  }

  return false;
}

/**
 * Check if the current path is a protected route
 */
function isProtectedRoute(pathname: string): boolean {
  return protectedRoutes.some(route =>
    pathname === route || pathname.startsWith(route + '/')
  );
}

/**
 * Check if the current path is a public-only route (should redirect if authenticated)
 */
function isPublicOnlyRoute(pathname: string): boolean {
  return publicOnlyRoutes.includes(pathname);
}

export default async function middleware(request: NextRequest, event: NextFetchEvent) {
  const { pathname } = request.nextUrl;

  // Skip middleware for static files, API routes, and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') ||
    pathname.startsWith('/auth/') // Skip auth pages (forgot-password, reset-password, signout)
  ) {
    return NextResponse.next();
  }

  // Handle Clerk authentication
  if (authSystem === 'clerk' && clerkMiddleware) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return clerkMiddleware((auth: any) => {
      const { userId } = auth();
      const isUserAuthenticated = !!userId;

      if (isProtectedRoute(pathname) && !isUserAuthenticated) {
        // Redirect to root page for unauthenticated users trying to access protected routes
        return NextResponse.redirect(new URL('/', request.url));
      }

      if (isPublicOnlyRoute(pathname) && isUserAuthenticated) {
        // Redirect to home for authenticated users trying to access public-only routes
        return NextResponse.redirect(new URL('/home', request.url));
      }

      return NextResponse.next();
    })(request, event);
  }

  // Handle email_password authentication
  if (authSystem === 'email_password') {
    const isUserAuthenticated = isAuthenticated(request);

    if (isProtectedRoute(pathname) && !isUserAuthenticated) {
      // Redirect to root page for unauthenticated users trying to access protected routes
      return NextResponse.redirect(new URL('/', request.url));
    }

    if (isPublicOnlyRoute(pathname) && isUserAuthenticated) {
      // Redirect to home for authenticated users trying to access public-only routes
      return NextResponse.redirect(new URL('/home', request.url));
    }

    return NextResponse.next();
  }

  // For any other auth systems or undefined auth system, allow access but protect routes
  // This is a fallback - in production you'd want to be more strict
  if (isProtectedRoute(pathname)) {
    return NextResponse.redirect(new URL('/', request.url));
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