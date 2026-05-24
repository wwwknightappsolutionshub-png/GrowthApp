'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Copy, ExternalLink, Gift, Smartphone } from 'lucide-react'
import { toast } from 'sonner'

import { bookings } from '@/lib/api-client'

function copy(text: string) {
  navigator.clipboard.writeText(text)
  toast.success('Copied')
}

export function LoyaltyPublicLinksBanner() {
  const { data: links } = useQuery({
    queryKey: ['bookings', 'links'],
    queryFn: () =>
      bookings.getLinks().then(
        (r) =>
          r.data as {
            memberships_url?: string
            rewards_portal_url?: string
          },
      ),
  })

  if (!links?.memberships_url && !links?.rewards_portal_url) return null

  return (
    <div className="rounded-xl border border-brand-teal-500/25 bg-brand-teal-950/30 p-4 space-y-3">
      <p className="text-sm font-semibold text-white">Membership &amp; rewards links</p>
      <p className="text-xs text-brand-teal-100/70">
        Share these with customers — enquiries from the memberships page appear here as leads.
      </p>
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {links.memberships_url ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2">
            <Gift className="h-4 w-4 shrink-0 text-brand-teal-300" />
            <span className="min-w-0 flex-1 truncate text-xs text-brand-teal-50">
              {links.memberships_url}
            </span>
            <button
              type="button"
              onClick={() => copy(links.memberships_url!)}
              className="shrink-0 text-brand-teal-300 hover:text-white"
              aria-label="Copy memberships link"
            >
              <Copy className="h-3.5 w-3.5" />
            </button>
            <a
              href={links.memberships_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-brand-teal-300 hover:text-white"
              aria-label="Open memberships page"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        ) : null}
        {links.rewards_portal_url ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2">
            <Smartphone className="h-4 w-4 shrink-0 text-brand-teal-300" />
            <span className="min-w-0 flex-1 truncate text-xs text-brand-teal-50">
              {links.rewards_portal_url}
            </span>
            <button
              type="button"
              onClick={() => copy(links.rewards_portal_url!)}
              className="shrink-0 text-brand-teal-300 hover:text-white"
              aria-label="Copy rewards wallet link"
            >
              <Copy className="h-3.5 w-3.5" />
            </button>
            <a
              href={links.rewards_portal_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-brand-teal-300 hover:text-white"
              aria-label="Open rewards wallet"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        ) : null}
      </div>
      <Link
        href="/dashboard/membership-rewards?section=landing"
        className="inline-block text-xs font-medium text-brand-teal-300 hover:text-white"
      >
        Edit memberships landing →
      </Link>
    </div>
  )
}
