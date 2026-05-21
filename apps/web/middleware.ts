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

const BUSINESS_SITE_BASE =
  process.env.BUSINESS_SITE_BASE_DOMAIN || 'customerflowai.online'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const host = (request.headers.get('host') || '').split(':')[0].toLowerCase()

  // Tenant subdomain: acme-plumbing.customerflowai.online → /sites/acme-plumbing
  if (
    host.endsWith(`.${BUSINESS_SITE_BASE}`) &&
    host !== BUSINESS_SITE_BASE &&
    host !== `www.${BUSINESS_SITE_BASE}` &&
    host !== `api.${BUSINESS_SITE_BASE}`
  ) {
    const slug = host.slice(0, -(BUSINESS_SITE_BASE.length + 1))
    if (slug && !slug.includes('.')) {
      const rewritePath =
        pathname === '/' || pathname === ''
          ? `/sites/${slug}`
          : `/sites/${slug}${pathname}`
      return NextResponse.rewrite(new URL(rewritePath, request.url))
    }
  }

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
    pathname.startsWith('/sites/') ||
    pathname.startsWith('/book/') ||
    pathname.startsWith('/embed/') ||
    // Public tenant pages, e.g. "/acme-plumbing" — exclude reserved app routes
    (/^\/[a-z0-9][a-z0-9-]*(\/.*)?$/.test(pathname)
      && !pathname.startsWith(DASHBOARD_PREFIX)
      && !pathname.startsWith(ADMIN_PREFIX)
      && !PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`)))
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
