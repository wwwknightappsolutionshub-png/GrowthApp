'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AuthGate } from '@/components/AuthGate'
import { loyaltyPortal } from '@/lib/api-client'

function formatWhen(iso: string | null) {
  if (!iso) return ''
  return new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(iso))
}

export default function RewardsPage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const qc = useQueryClient()
  const [lastCode, setLastCode] = useState<{ reward_name?: string; fulfillment_code?: string; code_expires_at?: string } | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['loyalty-rewards', tenant],
    queryFn: () => loyaltyPortal.rewards(tenant).then((r) => r.data),
  })
  const { data: profile } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortal.me(tenant).then((r) => r.data),
  })
  const { data: pending } = useQuery({
    queryKey: ['loyalty-pending-redemptions', tenant],
    queryFn: () => loyaltyPortal.pendingRedemptions(tenant).then((r) => r.data),
  })

  const redeem = useMutation({
    mutationFn: (id: string) => loyaltyPortal.redeem(tenant, id).then((r) => r.data),
    onSuccess: (result) => {
      setLastCode(result)
      toast.success(`Redeemed ${result.reward_name ?? 'reward'}! Show your code in store.`)
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
      void qc.invalidateQueries({ queryKey: ['loyalty-pending-redemptions', tenant] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail ?? 'Redemption failed')
    },
  })

  return (
    <AuthGate tenant={tenant}>
      <div className="space-y-3">
        <h1 className="text-lg font-semibold text-brand">Rewards catalog</h1>

        {lastCode?.fulfillment_code ? (
          <section className="card card-accent text-center">
            <p className="text-sm font-semibold text-brand">Your redemption code</p>
            <p className="mt-2 font-mono text-2xl font-bold tracking-widest text-brand">{lastCode.fulfillment_code}</p>
            <p className="mt-2 text-xs text-muted">
              Show this code to staff for {lastCode.reward_name ?? 'your reward'}.
              {lastCode.code_expires_at ? ` Valid until ${formatWhen(lastCode.code_expires_at)}.` : ''}
            </p>
          </section>
        ) : null}

        {pending?.items.length ? (
          <section className="card space-y-2">
            <h2 className="text-sm font-semibold text-brand">Pending in-store pickup</h2>
            {pending.items.map((item) => (
              <div key={item.id} className="rounded-lg border bg-white/80 p-3 text-sm">
                <p className="font-medium">{item.reward_name}</p>
                <p className="mt-1 font-mono text-lg tracking-wider text-brand">{item.fulfillment_code}</p>
                <p className="mt-1 text-xs text-muted">{item.points_spent} pts · expires {formatWhen(item.code_expires_at)}</p>
              </div>
            ))}
          </section>
        ) : null}

        {isLoading ? (
          <p className="text-sm text-muted">Loading rewards…</p>
        ) : data?.items.length ? (
          data.items.map((item) => {
            const canAfford = (profile?.points_balance ?? 0) >= item.points_cost
            const outOfStock = item.stock_remaining != null && item.stock_remaining <= 0
            return (
              <article key={item.id} className="card flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-brand">{item.name}</h2>
                  {item.description ? <p className="mt-1 text-sm text-muted">{item.description}</p> : null}
                  <p className="mt-2 text-sm font-medium text-accent">{item.points_cost.toLocaleString()} pts</p>
                </div>
                <button type="button" className="btn-primary shrink-0 text-xs" disabled={!canAfford || outOfStock || redeem.isPending} onClick={() => redeem.mutate(item.id)}>
                  {outOfStock ? 'Out of stock' : 'Redeem'}
                </button>
              </article>
            )
          })
        ) : (
          <p className="text-sm text-muted">No rewards available yet.</p>
        )}
      </div>
    </AuthGate>
  )
}
