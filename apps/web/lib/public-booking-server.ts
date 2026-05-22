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

export type PublicWidgetLoadResult = {
  widget: PublicWidgetPayload | null
  /** ok = tenant found; not_found = inactive/unknown slug; error = network/5xx; skipped = no INTERNAL_API_URL */
  status: 'ok' | 'not_found' | 'error' | 'skipped'
}

export function publicApiBase(): string | null {
  return (
    process.env.INTERNAL_API_URL ||
    process.env.API_PROXY_TARGET ||
    (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : null)
  )
}

export async function fetchPublicBookingWidget(slug: string): Promise<PublicWidgetLoadResult> {
  const base = publicApiBase()
  if (!base || !slug) {
    return { widget: null, status: 'skipped' }
  }
  try {
    const res = await fetch(`${base}/api/v1/public/booking/${encodeURIComponent(slug)}/widget`, {
      cache: 'no-store',
    })
    if (res.status === 404) {
      return { widget: null, status: 'not_found' }
    }
    if (!res.ok) {
      return { widget: null, status: 'error' }
    }
    const widget = (await res.json()) as PublicWidgetPayload
    if (widget?.error === 'not_found' || (!widget?.tenant_slug && !widget?.tenant_name)) {
      return { widget: null, status: 'not_found' }
    }
    return { widget, status: 'ok' }
  } catch {
    return { widget: null, status: 'error' }
  }
}
