'use client'

import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Award, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'
import { formatDate } from '@/lib/utils'

export function CustomerLoyaltyPanel({ customerId }: { customerId: string }) {
  const qc = useQueryClient()

  const { data: status } = useQuery({
    queryKey: ['membership-rewards-status'],
    queryFn: async () => (await membershipRewards.status()).data,
  })

  const loyaltyQ = useQuery({
    queryKey: ['mr-customer-loyalty', customerId],
    queryFn: async () => (await membershipRewards.customerLoyalty(customerId)).data,
    enabled: !!status?.has_membership_rewards,
  })

  const ledgerQ = useQuery({
    queryKey: ['mr-customer-ledger', customerId],
    queryFn: async () => (await membershipRewards.customerLedger(customerId, 15)).data,
    enabled: !!status?.has_membership_rewards && !!loyaltyQ.data,
  })

  const catalogQ = useQuery({
    queryKey: ['mr-catalog'],
    queryFn: async () => (await membershipRewards.listCatalog()).data.items,
    enabled: !!status?.has_membership_rewards,
  })

  const redeem = useMutation({
    mutationFn: (catalogItemId: string) => membershipRewards.redeemReward(customerId, catalogItemId),
    onSuccess: () => {
      toast.success('Reward redeemed')
      qc.invalidateQueries({ queryKey: ['mr-customer-loyalty', customerId] })
      qc.invalidateQueries({ queryKey: ['mr-customer-ledger', customerId] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not redeem'),
  })

  if (!status?.has_membership_rewards) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
        <p className="flex items-center gap-2 font-medium text-foreground">
          <Award className="h-4 w-4" /> Loyalty program
        </p>
        <p className="mt-1">
          Enable{' '}
          <Link href="/dashboard/membership-rewards" className="text-brand-teal-600 hover:underline">
            Membership & Rewards
          </Link>{' '}
          to track points for this customer.
        </p>
      </div>
    )
  }

  if (loyaltyQ.isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-brand-teal-500" />
      </div>
    )
  }

  const loyalty = loyaltyQ.data
  const affordable = (catalogQ.data ?? []).filter(
    (item) => item.is_active && loyalty && item.points_cost <= loyalty.points_balance,
  )

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Award className="h-4 w-4 text-brand-teal-600" /> Loyalty
          </p>
          <p className="mt-1 text-2xl font-bold text-foreground">{loyalty?.points_balance ?? 0} pts</p>
          <p className="text-xs text-muted-foreground capitalize">
            {loyalty?.tier_code ?? 'bronze'} tier · {loyalty?.points_lifetime ?? 0} lifetime
          </p>
        </div>
        <Link
          href="/dashboard/membership-rewards?section=customers"
          className="text-xs font-medium text-brand-teal-600 hover:underline"
        >
          Manage
        </Link>
      </div>

      {affordable.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">Redeem for customer</p>
          <div className="flex flex-wrap gap-2">
            {affordable.slice(0, 4).map((item) => (
              <button
                key={item.id}
                type="button"
                disabled={redeem.isPending}
                onClick={() => redeem.mutate(item.id)}
                className="rounded-md border border-border bg-background px-2 py-1 text-xs hover:bg-muted disabled:opacity-50"
              >
                {item.name} ({item.points_cost} pts)
              </button>
            ))}
          </div>
        </div>
      )}

      {ledgerQ.data && ledgerQ.data.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">Recent activity</p>
          <ul className="space-y-1.5 max-h-40 overflow-y-auto">
            {ledgerQ.data.slice(0, 8).map((entry) => (
              <li key={entry.id} className="flex justify-between text-xs gap-2">
                <span className="text-muted-foreground truncate">
                  {entry.description || entry.source}
                </span>
                <span className={entry.amount >= 0 ? 'text-emerald-600' : 'text-red-500'}>
                  {entry.amount >= 0 ? '+' : ''}
                  {entry.amount}
                </span>
              </li>
            ))}
          </ul>
          {ledgerQ.data[0]?.created_at && (
            <p className="text-[10px] text-muted-foreground mt-2">
              Last update {formatDate(ledgerQ.data[0].created_at)}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
