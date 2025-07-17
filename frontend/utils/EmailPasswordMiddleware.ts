import { User } from '@/types/User';
import { NextRequest, NextResponse } from 'next/server';

// Configuration
const LOGIN_URL = '/';

/**
 * Check if user is authenticated (email_password only)
 */
async function isEmailPasswordAuthenticated(request: NextRequest): Promise<boolean> {
  const accessToken = request.cookies.get('access_token');
  const apiBaseUrl = process.env.API_BASE_URL;
  const res = await fetch(`${apiBaseUrl}/users/me`, {
    headers: { 'Authorization': `Bearer ${accessToken?.value}` }
  })
  const user = await res.json() as User;
  return !!accessToken?.value && user && user.uuid ? true : false;
}

export default async function EmailPasswordMiddleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === LOGIN_URL) {
    return NextResponse.next();
  }

  const isUserAuthenticated = await isEmailPasswordAuthenticated(request);
  if (isUserAuthenticated) {
    return NextResponse.next();
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