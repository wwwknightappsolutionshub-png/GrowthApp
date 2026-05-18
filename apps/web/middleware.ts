import { NextRequest, NextResponse } from 'next/server'

/**
 * Server-side route guard.
 *
 * Authentication is cookie-based: the API issues `access_token` and
 * `refresh_token` as httpOnly cookies. Here we do a presence check on every
 * dashboard request — if neither cookie is present the user is bounced to
 * `/login` before any protected page even renders.
 *
 * We don't try to *verify* the JWT here: that would require the secret and
 * would duplicate API logic. We just gate on presence. The actual verification
 * happens on every API call.
 */

const PUBLIC_PREFIXES = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-2fa',
  '/pricing',
  '/privacy',
  '/terms',
]

const DASHBOARD_PREFIX = '/dashboard'
const ADMIN_PREFIX = '/admin'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (
    pathname === '/' ||
    PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`)) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/favicon') ||
    pathname === '/manifest.webmanifest' ||
    pathname === '/sw.js' ||
    pathname === '/offline.html' ||
    pathname.startsWith('/icons/') ||
    pathname.startsWith('/static') ||
    // Public tenant pages, e.g. "/acme-plumbing" or "/acme-plumbing/review/abc"
    (/^\/[a-z0-9][a-z0-9-]*(\/.*)?$/.test(pathname)
      && !pathname.startsWith(DASHBOARD_PREFIX)
      && !pathname.startsWith(ADMIN_PREFIX))
  ) {
    return NextResponse.next()
  }

  if (pathname.startsWith(DASHBOARD_PREFIX) || pathname.startsWith(ADMIN_PREFIX)) {
    const hasAccess = request.cookies.has('access_token')
    const hasRefresh = request.cookies.has('refresh_token')
    if (!hasAccess && !hasRefresh) {
      const redirectUrl = new URL('/login', request.url)
      redirectUrl.searchParams.set('next', pathname)
      return NextResponse.redirect(redirectUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
