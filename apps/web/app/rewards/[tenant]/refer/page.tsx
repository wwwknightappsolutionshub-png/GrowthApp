'use client'

import { useQuery } from '@tanstack/react-query'
import { ExternalLink, Users } from 'lucide-react'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'

function qrImageUrl(data: string, size = 160) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

export default function RewardsReferPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data: upsell, isLoading } = useQuery({
    queryKey: ['loyalty-upsell', tenant],
    queryFn: () => loyaltyPortalCustomer.upsell(tenant).then((r) => r.data),
  })
  const { data: profile } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortalCustomer.me(tenant).then((r) => r.data),
  })

  return (
    <LoyaltyAuthGate tenant={tenant}>
      <div className="space-y-4">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-brand">
          <Users className="h-5 w-5" />
          Refer &amp; Win
        </h1>

        {isLoading ? (
          <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading…</p>
        ) : upsell ? (
          <>
            <section className="card space-y-3">
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Share your referral link with friends. When they become a customer, you earn loyalty
                points.
              </p>
              <div className="flex flex-col items-center gap-3 rounded-lg border border-[hsl(var(--brand-teal)/0.25)] bg-[hsl(var(--brand-teal)/0.06)] p-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={qrImageUrl(upsell.refer_win_url)}
                  alt="Refer and Win QR code"
                  width={160}
                  height={160}
                  className="rounded-lg bg-white p-2"
                />
                <p className="break-all text-center text-xs text-[hsl(var(--muted-foreground))]">{upsell.refer_win_url}</p>
              </div>
              <a
                href={upsell.refer_win_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary inline-flex w-full items-center justify-center gap-2"
              >
                Open referral form
                <ExternalLink className="h-4 w-4" />
              </a>
            </section>

            {profile ? (
              <section className="card text-sm text-[hsl(var(--muted-foreground))]">
                <p>
                  Referring as{' '}
                  <span className="font-medium text-[hsl(var(--foreground))]">
                    {profile.first_name} {profile.last_name ?? ''}
                  </span>
                  {profile.phone ? ` · ${profile.phone}` : ''}
                </p>
                <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                  Use the same name and phone on the referral form so we can credit your account.
                </p>
              </section>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-red-600">Could not load referral details.</p>
        )}
      </div>
    </LoyaltyAuthGate>
  )
}
