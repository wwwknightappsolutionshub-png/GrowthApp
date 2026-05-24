'use client'

import { useQuery } from '@tanstack/react-query'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'

export default function RewardsDashboardPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortalCustomer.me(tenant).then((r) => r.data),
  })

  return (
    <LoyaltyAuthGate tenant={tenant}>
      {isLoading ? (
        <p className="text-sm text-slate-500">Loading your wallet…</p>
      ) : data ? (
        <div className="space-y-4">
          <section className="card text-center">
            <p className="text-sm text-slate-500">Available points</p>
            <p className="mt-1 text-4xl font-bold tabular-nums">{data.points_balance.toLocaleString()}</p>
            <p className="mt-2 text-xs text-slate-500">
              Lifetime {data.points_lifetime.toLocaleString()} pts · {data.tier_name} tier
            </p>
          </section>

          <section className="card">
            <h2 className="text-sm font-semibold">Hi {data.first_name}!</h2>
            <p className="mt-1 text-sm text-slate-600">
              Redeem rewards, show your QR in store, and track your points history.
            </p>
            {Array.isArray(data.tier_benefits) && data.tier_benefits.length > 0 ? (
              <ul className="mt-3 space-y-1 text-sm text-slate-600">
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
