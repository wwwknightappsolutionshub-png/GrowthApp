'use client'

import { ExternalLink, Star } from 'lucide-react'

function qrImageUrl(data: string, size = 160) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

type Props = {
  reviewUrl: string
  tenantName?: string
  compact?: boolean
}

export function GoogleReviewCard({ reviewUrl, tenantName, compact = false }: Props) {
  return (
    <section className={compact ? 'card card-review space-y-3' : 'card card-review space-y-4'}>
      <div className="flex items-start gap-3">
        <Star className="mt-0.5 h-5 w-5 shrink-0 text-[hsl(var(--brand-teal))]" fill="currentColor" />
        <div className="flex-1">
          <p className="font-semibold text-brand">Review &amp; win</p>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            {tenantName
              ? `Leave ${tenantName} a Google review and earn loyalty points.`
              : 'Leave us a Google review and earn loyalty points.'}
          </p>
        </div>
      </div>

      <div className="flex flex-col items-center gap-3 rounded-lg border border-[hsl(var(--brand-teal)/0.25)] bg-white/80 p-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={qrImageUrl(reviewUrl, compact ? 140 : 160)}
          alt="Google review QR code"
          width={compact ? 140 : 160}
          height={compact ? 140 : 160}
          className="rounded-lg border border-[hsl(var(--border))] bg-white p-2"
        />
        <p className="text-center text-xs text-[hsl(var(--muted-foreground))]">
          Scan to open Google reviews on your phone
        </p>
      </div>

      <a
        href={reviewUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-accent inline-flex w-full items-center justify-center gap-2"
      >
        Review now
        <ExternalLink className="h-4 w-4" />
      </a>
    </section>
  )
}
