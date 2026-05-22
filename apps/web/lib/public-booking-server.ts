/** Server-only fetch for public booking widget (SSR + initial client data). */

export type PublicWidgetPayload = {
  tenant_slug?: string
  tenant_name?: string
  widget_primary_color?: string
  booking_form?: { version?: number; fields?: unknown[] }
  services?: { id: string; name: string; duration_minutes?: number; deposit_pence?: number }[]
  deposit_enabled?: boolean
  default_deposit_pence?: number
  error?: string
}

function apiBase(): string | null {
  return (
    process.env.INTERNAL_API_URL ||
    process.env.API_PROXY_TARGET ||
    (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : null)
  )
}

export async function fetchPublicBookingWidget(slug: string): Promise<PublicWidgetPayload | null> {
  const base = apiBase()
  if (!base || !slug) return null
  try {
    const res = await fetch(`${base}/api/v1/public/booking/${encodeURIComponent(slug)}/widget`, {
      cache: 'no-store',
    })
    if (!res.ok) return null
    return (await res.json()) as PublicWidgetPayload
  } catch {
    return null
  }
}
