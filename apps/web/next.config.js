/** @type {import('next').NextConfig} */
const API_ORIGIN = process.env.API_PROXY_TARGET || 'http://localhost:8000'

const nextConfig = {
  // Use standard output instead of standalone to avoid Windows symlink issues
  output: undefined,
  images: {
    unoptimized: true,
    remotePatterns: [
      { protocol: 'https', hostname: '**' }
    ]
  },
  // Proxy /api/v1/* and /healthz/* to the FastAPI server. This keeps everything
  // on a single origin so httpOnly cookies (access_token + refresh_token) are
  // visible to both the Next.js middleware and the browser fetch layer without
  // any cross-origin / SameSite gymnastics. In production set
  // NEXT_PUBLIC_API_URL='' so the apiClient uses relative `/api/v1/*` URLs and
  // the upstream API_PROXY_TARGET points at the internal API service.
  async rewrites() {
    return [
      { source: '/api/v1/:path*', destination: `${API_ORIGIN}/api/v1/:path*` },
      { source: '/api/referrals/:path*', destination: `${API_ORIGIN}/api/referrals/:path*` },
      { source: '/api/superadmin/:path*', destination: `${API_ORIGIN}/api/superadmin/:path*` },
      { source: '/api/super-admin/:path*', destination: `${API_ORIGIN}/api/super-admin/:path*` },
      { source: '/api/admin/:path*', destination: `${API_ORIGIN}/api/admin/:path*` },
      { source: '/healthz',       destination: `${API_ORIGIN}/healthz` },
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
