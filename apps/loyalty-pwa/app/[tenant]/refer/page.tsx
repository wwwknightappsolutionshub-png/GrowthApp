'use client'

import { useQuery } from '@tanstack/react-query'
import { ExternalLink, Users } from 'lucide-react'
import { AuthGate } from '@/components/AuthGate'
import { loyaltyPortal } from '@/lib/api-client'

function qrImageUrl(data: string) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(data)}`
}

export default function ReferPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data: upsell, isLoading } = useQuery({
    queryKey: ['loyalty-upsell', tenant],
    queryFn: () => loyaltyPortal.upsell(tenant).then((r) => r.data),
  })
  const { data: profile } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortal.me(tenant).then((r) => r.data),
  })

  return (
    <AuthGate tenant={tenant}>
      <div className="space-y-4">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-brand">
          <Users className="h-5 w-5" /> Refer &amp; Win
        </h1>
        {isLoading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : upsell ? (
          <>
            <section className="card space-y-3">
              <p className="text-sm text-muted">Share your referral link. When friends become customers, you earn bonus points.</p>
              <div className="flex flex-col items-center gap-3 rounded-lg border bg-white/80 p-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={qrImageUrl(upsell.refer_win_url)} alt="Refer QR" width={160} height={160} className="rounded-lg bg-white p-2" />
                <p className="break-all text-center text-xs text-muted">{upsell.refer_win_url}</p>
              </div>
              <a href={upsell.refer_win_url} target="_blank" rel="noopener noreferrer" className="btn-primary inline-flex w-full items-center justify-center gap-2">
                Open referral form <ExternalLink className="h-4 w-4" />
              </a>
            </section>
            {profile ? (
              <section className="card text-sm text-muted">
                Referring as <span className="font-medium text-[var(--foreground)]">{profile.first_name} {profile.last_name ?? ''}</span>
              </section>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-red-600">Could not load referral details.</p>
        )}
      </div>
    </AuthGate>
  )
}
