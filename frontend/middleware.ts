// If you want to use EmailPasswordMiddleware instead of Clerk, uncomment the following lines
// import { NextRequest } from 'next/server';
// import EmailPasswordMiddleware from '@/utils/EmailPasswordMiddleware';
// const middleware = (request: NextRequest) => EmailPasswordMiddleware(request);
// export default middleware;

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