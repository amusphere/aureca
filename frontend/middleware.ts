// If you want to use EmailPasswordMiddleware instead of Clerk, uncomment the following lines
// import { NextRequest } from 'next/server';
// import EmailPasswordMiddleware from '@/utils/EmailPasswordMiddleware';
// const middleware = (request: NextRequest) => EmailPasswordMiddleware(request);
// export default middleware;

import { clerkMiddleware } from '@clerk/nextjs/server';

export default clerkMiddleware((auth, req) => {
  // デモページは認証不要
  if (req.nextUrl.pathname.startsWith('/demo')) {
    return;
  }

  // その他のページは通常の認証処理
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}