// If you want to use EmailPasswordMiddleware instead of Clerk, uncomment the following lines
// import { NextRequest } from 'next/server';
// import EmailPasswordMiddleware from '@/utils/EmailPasswordMiddleware';
// const middleware = (request: NextRequest) => EmailPasswordMiddleware(request);
// export default middleware;

import { clerkMiddleware } from '@clerk/nextjs/server';
export default clerkMiddleware();

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}