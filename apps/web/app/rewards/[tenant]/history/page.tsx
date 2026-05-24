'use client'

import { useQuery } from '@tanstack/react-query'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'

function formatWhen(iso: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export default function RewardsHistoryPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-history', tenant],
    queryFn: () => loyaltyPortalCustomer.history(tenant).then((r) => r.data),
  })

  return (
    <LoyaltyAuthGate tenant={tenant}>
      <div className="space-y-3">
        <h1 className="text-lg font-semibold">Points history</h1>
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading history…</p>
        ) : data?.items.length ? (
          <ul className="space-y-2">
            {data.items.map((entry) => (
              <li key={entry.id} className="card flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">
                    {entry.description ?? entry.source.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-slate-500">{formatWhen(entry.created_at)}</p>
                  {entry.expires_at ? (
                    <p className="text-xs text-amber-600">Expires {formatWhen(entry.expires_at)}</p>
                  ) : null}
                </div>
                <div className="text-right">
                  <p
                    className={`text-sm font-semibold tabular-nums ${
                      entry.amount >= 0 ? 'text-emerald-600' : 'text-red-600'
                    }`}
                  >
                    {entry.amount >= 0 ? '+' : ''}
                    {entry.amount}
                  </p>
                  <p className="text-xs text-slate-500">Bal {entry.balance_after}</p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">No activity yet.</p>
        )}
      </div>
    </LoyaltyAuthGate>
  )
}
