'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { ExternalLink, Gift, Star, Users } from 'lucide-react'
import { AuthGate } from '@/components/AuthGate'
import { loyaltyPortal } from '@/lib/api-client'

export default function DashboardPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortal.me(tenant).then((r) => r.data),
  })
  const { data: upsell } = useQuery({
    queryKey: ['loyalty-upsell', tenant],
    queryFn: () => loyaltyPortal.upsell(tenant).then((r) => r.data),
  })

  return (
    <AuthGate tenant={tenant}>
      {isLoading ? (
        <p className="text-sm text-muted">Loading your wallet…</p>
      ) : data ? (
        <div className="space-y-4">
          <section className="card text-center">
            <p className="text-sm text-muted">Available points</p>
            <p className="mt-1 text-4xl font-bold tabular-nums text-brand">{data.points_balance.toLocaleString()}</p>
            <p className="mt-2 text-xs text-muted">
              Lifetime {data.points_lifetime.toLocaleString()} pts · {data.tier_name} tier
            </p>
          </section>

          <section className="card grid grid-cols-3 gap-2 text-center text-xs">
            <div><p className="text-muted">Earned</p><p className="mt-1 font-semibold tabular-nums">{data.points_earned.toLocaleString()}</p></div>
            <div><p className="text-muted">Redeemed</p><p className="mt-1 font-semibold tabular-nums">{data.points_redeemed.toLocaleString()}</p></div>
            <div><p className="text-muted">Expiring</p><p className="mt-1 font-semibold tabular-nums text-amber-700">{data.points_expiring_soon.toLocaleString()}</p></div>
          </section>

          {data.next_tier_name ? (
            <section className="card space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Progress to {data.next_tier_name}</span>
                <span className="text-muted">{data.tier_progress_percent}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                <div className="progress-fill h-full rounded-full" style={{ width: `${data.tier_progress_percent}%` }} />
              </div>
              <p className="text-xs text-muted">{data.points_to_next_tier.toLocaleString()} points until {data.next_tier_name}</p>
            </section>
          ) : null}

          {data.pending_redemptions > 0 ? (
            <section className="card text-sm text-amber-900 bg-amber-50 border-amber-200">
              You have {data.pending_redemptions} pending reward{data.pending_redemptions === 1 ? '' : 's'} — show your code in store.
            </section>
          ) : null}

          {upsell?.google_review_available && upsell.google_review_url ? (
            <section className="card card-review">
              <div className="flex items-start gap-3">
                <Star className="h-5 w-5 text-accent" fill="currentColor" />
                <div className="flex-1">
                  <p className="font-semibold text-brand">Review &amp; win</p>
                  <p className="mt-1 text-sm text-muted">Leave a Google review and earn loyalty points.</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <a href={upsell.google_review_url} target="_blank" rel="noopener noreferrer" className="btn-accent inline-flex items-center gap-1 text-xs">
                      Review now <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                    <Link href={`/${tenant}/profile`} className="btn-secondary inline-flex text-xs">Show QR code</Link>
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          {upsell?.has_membership_plans && !upsell.active_subscription ? (
            <section className="card card-accent">
              <div className="flex items-start gap-3">
                <Gift className="h-5 w-5 text-brand" />
                <div>
                  <p className="font-semibold text-brand">Upgrade membership</p>
                  <p className="mt-1 text-sm text-muted">Unlock exclusive discounts and member perks.</p>
                  <a href={upsell.memberships_url} className="btn-primary mt-3 inline-flex items-center gap-1 text-xs">
                    View plans <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </div>
            </section>
          ) : null}

          <section className="card card-accent flex items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <Users className="h-5 w-5 text-brand" />
              <div>
                <p className="font-semibold text-brand">Refer &amp; Win</p>
                <p className="mt-1 text-sm text-muted">Refer friends and earn bonus points.</p>
              </div>
            </div>
            <Link href={`/${tenant}/refer`} className="btn-secondary shrink-0 text-xs">Refer</Link>
          </section>

          <section className="card">
            <h2 className="text-sm font-semibold text-brand">Hi {data.first_name}!</h2>
            <p className="mt-1 text-sm text-muted">Redeem rewards, show your QR in store, and track your points history.</p>
          </section>
        </div>
      ) : (
        <p className="text-sm text-red-600">Could not load your profile.</p>
      )}
    </AuthGate>
  )
}
