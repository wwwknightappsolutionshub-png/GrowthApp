import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

/** Dynamic manifest — uses tenant logo when white-label PWA addon is active. */
export async function GET() {
  const cookieStore = await cookies()
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join('; ')

  let icons = [
    { src: '/icons/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
    { src: '/icons/pwa-icon.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any' },
    { src: '/icons/maskable-icon.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'maskable' },
  ]
  let name = 'CustomerFlowai'
  let shortName = 'CustomerFlowai'
  let themeColor = '#025422'

  try {
    const res = await fetch(`${API_BASE}/pwa/branding`, {
      headers: cookieHeader ? { cookie: cookieHeader } : {},
      cache: 'no-store',
    })
    if (res.ok) {
      const data = (await res.json()) as {
        enabled?: boolean
        name?: string
        short_name?: string
        theme_color?: string
        icon_url?: string | null
      }
      if (data.enabled) {
        name = data.name || name
        shortName = data.short_name || shortName
        themeColor = data.theme_color || themeColor
        if (data.icon_url) {
          icons = [
            { src: data.icon_url, sizes: '512x512', type: 'image/png', purpose: 'any' },
            ...icons,
          ]
        }
      }
    }
  } catch {
    // fall back to default manifest fields
  }

  return NextResponse.json(
    {
      name,
      short_name: shortName,
      description: 'Give customers a rewards wallet and run your business from one mobile workspace.',
      start_url: '/dashboard?source=pwa',
      scope: '/',
      display: 'standalone',
      background_color: '#02140a',
      theme_color: themeColor,
      orientation: 'portrait',
      icons,
      shortcuts: [
        { name: 'Dashboard', url: '/dashboard' },
        { name: 'Leads', url: '/dashboard/leads' },
        { name: 'Bookings', url: '/dashboard/bookings' },
        { name: 'Quotes', url: '/dashboard/quotes' },
        { name: 'Invoices', url: '/dashboard/invoices' },
        { name: 'Customer wallet', url: '/dashboard/membership-rewards' },
      ],
    },
    { headers: { 'Content-Type': 'application/manifest+json' } },
  )
}
