/**
 * Shared SEO helpers — canonical URLs, reserved slugs, and site base URL.
 */

export const SITE_URL =
  process.env.NEXT_PUBLIC_APP_URL ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'https://customerflowai.online')

/** Paths that must never be treated as tenant slugs (see app/(public)/[tenantSlug]). */
export const RESERVED_PUBLIC_SLUGS = new Set([
  'robots.txt',
  'sitemap.xml',
  'favicon.ico',
  'manifest.webmanifest',
  'sw.js',
  'offline.html',
  'apple-icon',
  'icon',
  'opengraph-image',
  'twitter-image',
])

export function canonical(path = '/'): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return new URL(normalized, SITE_URL).toString()
}

export const DEFAULT_OG_IMAGE = {
  url: '/opengraph-image',
  width: 1200,
  height: 630,
  alt: 'CustomerFlowai — AI operating system for UK businesses',
} as const
