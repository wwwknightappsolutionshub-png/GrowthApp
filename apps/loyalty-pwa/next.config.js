/** @type {import('next').NextConfig} */
const API_ORIGIN = process.env.API_PROXY_TARGET || 'http://localhost:8000'

const nextConfig = {
  basePath: '/rewards',
  images: { unoptimized: true },
  async rewrites() {
    return [{ source: '/api/v1/:path*', destination: `${API_ORIGIN}/api/v1/:path*` }]
  },
}

module.exports = nextConfig
