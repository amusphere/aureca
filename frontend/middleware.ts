import { clerkMiddleware } from '@clerk/nextjs/server';

export default clerkMiddleware();

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