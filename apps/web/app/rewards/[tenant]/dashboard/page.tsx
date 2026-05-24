'use client'

import { useQuery } from '@tanstack/react-query'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { LoyaltyUpsellSection } from '@/components/loyalty-portal/LoyaltyUpsellSection'
import { loyaltyPortalCustomer } from '@/lib/api-client'

export default function RewardsDashboardPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortalCustomer.me(tenant).then((r) => r.data),
  })
  const { data: upsell, isLoading: upsellLoading } = useQuery({
    queryKey: ['loyalty-upsell', tenant],
    queryFn: () => loyaltyPortalCustomer.upsell(tenant).then((r) => r.data),
  })

  return (
    <LoyaltyAuthGate tenant={tenant}>
      {isLoading ? (
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Loading your wallet…</p>
      ) : data ? (
        <div className="space-y-4">
          <section className="card text-center">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">Available points</p>
            <p className="mt-1 text-4xl font-bold tabular-nums text-brand">{data.points_balance.toLocaleString()}</p>
            <p className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
              Lifetime {data.points_lifetime.toLocaleString()} pts · {data.tier_name} tier
            </p>
          </section>

          <section className="card grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <p className="text-[hsl(var(--muted-foreground))]">Earned</p>
              <p className="mt-1 font-semibold tabular-nums">{data.points_earned.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[hsl(var(--muted-foreground))]">Redeemed</p>
              <p className="mt-1 font-semibold tabular-nums">{data.points_redeemed.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[hsl(var(--muted-foreground))]">Expiring</p>
              <p className="mt-1 font-semibold tabular-nums text-[hsl(var(--warning))]">
                {data.points_expiring_soon.toLocaleString()}
              </p>
            </div>
          </section>

          {data.next_tier_name ? (
            <section className="card space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Progress to {data.next_tier_name}</span>
                <span className="text-[hsl(var(--muted-foreground))]">{data.tier_progress_percent}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[hsl(var(--muted))]">
                <div
                  className="progress-fill h-full rounded-full transition-all"
                  style={{ width: `${data.tier_progress_percent}%` }}
                />
              </div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                {data.points_to_next_tier.toLocaleString()} points until {data.next_tier_name}
              </p>
            </section>
          ) : (
            <section className="card text-sm text-[hsl(var(--muted-foreground))]">
              You&apos;ve reached the highest tier — keep earning to unlock more rewards.
            </section>
          )}

          {data.pending_redemptions > 0 ? (
            <section className="card border-[hsl(var(--warning)/0.35)] bg-[hsl(var(--warning)/0.08)] text-sm text-[hsl(var(--foreground))]">
              You have {data.pending_redemptions} pending reward
              {data.pending_redemptions === 1 ? '' : 's'} — show your redemption code in store.
            </section>
          ) : null}

          {!upsellLoading && upsell ? <LoyaltyUpsellSection tenant={tenant} upsell={upsell} /> : null}

          <section className="card">
            <h2 className="text-sm font-semibold text-brand">Hi {data.first_name}!</h2>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              Redeem rewards, show your QR in store, and track your points history.
            </p>
            {Array.isArray(data.tier_benefits) && data.tier_benefits.length > 0 ? (
              <ul className="mt-3 space-y-1 text-sm text-[hsl(var(--muted-foreground))]">
                {data.tier_benefits.slice(0, 4).map((b, i) => (
                  <li key={i}>• {typeof b === 'string' ? b : JSON.stringify(b)}</li>
                ))}
              </ul>
            ) : null}
          </section>
        </div>
      ) : (
        <p className="text-sm text-red-600">Could not load your profile.</p>
      )}
    </LoyaltyAuthGate>
  )
}
