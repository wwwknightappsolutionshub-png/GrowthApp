'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AuthGate } from '@/components/AuthGate'
import { loyaltyPortal } from '@/lib/api-client'

export default function RewardsPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-rewards', tenant],
    queryFn: () => loyaltyPortal.rewards(tenant).then((r) => r.data),
  })
  const { data: profile } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortal.me(tenant).then((r) => r.data),
  })

  const redeem = useMutation({
    mutationFn: (id: string) => loyaltyPortal.redeem(tenant, id).then((r) => r.data),
    onSuccess: (result) => {
      toast.success(`Redeemed ${result.reward_name ?? 'reward'}!`)
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
      void qc.invalidateQueries({ queryKey: ['loyalty-history', tenant] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail ?? 'Redemption failed')
    },
  })

  return (
    <AuthGate tenant={tenant}>
      <div className="space-y-3">
        <h1 className="text-lg font-semibold">Rewards catalog</h1>
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading rewards…</p>
        ) : data?.items.length ? (
          data.items.map((item) => {
            const canAfford = (profile?.points_balance ?? 0) >= item.points_cost
            const outOfStock = item.stock_remaining != null && item.stock_remaining <= 0
            return (
              <article key={item.id} className="card flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">{item.name}</h2>
                  {item.description ? (
                    <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                  ) : null}
                  <p className="mt-2 text-sm font-medium" style={{ color: 'var(--tenant-primary)' }}>
                    {item.points_cost.toLocaleString()} pts
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-primary shrink-0 text-xs"
                  disabled={!canAfford || outOfStock || redeem.isPending}
                  onClick={() => redeem.mutate(item.id)}
                >
                  {outOfStock ? 'Out of stock' : 'Redeem'}
                </button>
              </article>
            )
          })
        ) : (
          <p className="text-sm text-slate-500">No rewards available yet.</p>
        )}
      </div>
    </AuthGate>
  )
}
