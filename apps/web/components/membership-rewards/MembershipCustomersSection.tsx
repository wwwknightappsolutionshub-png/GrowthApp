'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Search } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'

export function MembershipCustomersSection() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [adjustAmount, setAdjustAmount] = useState('')
  const [adjustNote, setAdjustNote] = useState('')
  const [redeemItemId, setRedeemItemId] = useState('')

  const customersQ = useQuery({
    queryKey: ['mr-loyalty-customers', debouncedSearch],
    queryFn: async () =>
      (await membershipRewards.listLoyaltyCustomers({ search: debouncedSearch || undefined, limit: 50 })).data,
  })

  const catalogQ = useQuery({
    queryKey: ['mr-catalog'],
    queryFn: async () => (await membershipRewards.listCatalog()).data.items,
  })

  const ledgerQ = useQuery({
    queryKey: ['mr-customer-ledger', selectedId],
    queryFn: async () => (await membershipRewards.customerLedger(selectedId!, 30)).data,
    enabled: !!selectedId,
  })

  const adjust = useMutation({
    mutationFn: () =>
      membershipRewards.adjustPoints({
        customer_id: selectedId!,
        amount: parseInt(adjustAmount || '0', 10),
        source: 'adjustment',
        description: adjustNote || 'Manual adjustment',
      }),
    onSuccess: () => {
      toast.success('Points updated')
      setAdjustAmount('')
      setAdjustNote('')
      qc.invalidateQueries({ queryKey: ['mr-loyalty-customers'] })
      qc.invalidateQueries({ queryKey: ['mr-customer-ledger', selectedId] })
      qc.invalidateQueries({ queryKey: ['mr-analytics'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not adjust points'),
  })

  const redeem = useMutation({
    mutationFn: () => membershipRewards.redeemReward(selectedId!, redeemItemId),
    onSuccess: () => {
      toast.success('Reward redeemed')
      setRedeemItemId('')
      qc.invalidateQueries({ queryKey: ['mr-loyalty-customers'] })
      qc.invalidateQueries({ queryKey: ['mr-customer-ledger', selectedId] })
      qc.invalidateQueries({ queryKey: ['mr-redemptions'] })
      qc.invalidateQueries({ queryKey: ['mr-analytics'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not redeem'),
  })

  const selected = customersQ.data?.items.find((c) => c.customer_id === selectedId)

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <div className="lg:col-span-3 rounded-xl border border-white/10 bg-white/5 p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-white">Loyalty members</h2>
          <form
            className="relative flex-1 min-w-[200px] max-w-sm"
            onSubmit={(e) => {
              e.preventDefault()
              setDebouncedSearch(search.trim())
            }}
          >
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name, email, phone…"
              className="w-full rounded-lg border border-white/10 bg-brand-forest-950 pl-9 pr-3 py-2 text-sm text-white"
            />
          </form>
        </div>

        {customersQ.isLoading ? (
          <LoaderCenter />
        ) : (
          <>
            <p className="text-xs text-slate-500">{customersQ.data?.total ?? 0} members</p>
            <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-brand-forest-950/95">
                  <tr className="text-slate-400 border-b border-white/10">
                    <th className="py-2 text-left">Member</th>
                    <th className="py-2 text-right">Balance</th>
                    <th className="py-2 text-right">Tier</th>
                  </tr>
                </thead>
                <tbody>
                  {(customersQ.data?.items ?? []).map((row) => (
                    <tr
                      key={row.customer_id}
                      onClick={() => setSelectedId(row.customer_id)}
                      className={`border-b border-white/5 cursor-pointer ${
                        selectedId === row.customer_id ? 'bg-brand-teal-600/20' : 'hover:bg-white/5'
                      }`}
                    >
                      <td className="py-2.5 text-slate-200">
                        <p className="font-medium">{row.customer_name || '—'}</p>
                        <p className="text-xs text-slate-500">{row.email || row.phone || ''}</p>
                      </td>
                      <td className="py-2.5 text-right text-white">{row.points_balance}</td>
                      <td className="py-2.5 text-right capitalize text-slate-300">{row.tier_code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!customersQ.data?.items?.length && (
                <p className="text-sm text-slate-500 py-8 text-center">No loyalty members found.</p>
              )}
            </div>
          </>
        )}
      </div>

      <div className="lg:col-span-2 space-y-4">
        {selected ? (
          <>
            <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-2">
              <h3 className="font-semibold text-white">{selected.customer_name}</h3>
              <p className="text-3xl font-bold text-brand-teal-300">{selected.points_balance} pts</p>
              <p className="text-xs text-slate-400 capitalize">
                {selected.tier_code} · {selected.points_lifetime} lifetime
              </p>
              <Link
                href={`/dashboard/crm/customers/${selected.customer_id}`}
                className="inline-block text-xs text-brand-teal-300 hover:underline"
              >
                Open CRM profile →
              </Link>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-3">
              <h4 className="text-sm font-semibold text-white">Adjust points</h4>
              <input
                type="number"
                value={adjustAmount}
                onChange={(e) => setAdjustAmount(e.target.value)}
                placeholder="Amount (+ / −)"
                className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              />
              <input
                value={adjustNote}
                onChange={(e) => setAdjustNote(e.target.value)}
                placeholder="Note (optional)"
                className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              />
              <button
                type="button"
                disabled={adjust.isPending || !adjustAmount}
                onClick={() => adjust.mutate()}
                className="w-full rounded-lg bg-brand-teal-600 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
              >
                Apply adjustment
              </button>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-3">
              <h4 className="text-sm font-semibold text-white">Redeem reward</h4>
              <select
                value={redeemItemId}
                onChange={(e) => setRedeemItemId(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              >
                <option value="">Select reward</option>
                {(catalogQ.data ?? [])
                  .filter((i) => i.is_active && i.points_cost <= selected.points_balance)
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} — {item.points_cost} pts
                    </option>
                  ))}
              </select>
              <button
                type="button"
                disabled={redeem.isPending || !redeemItemId}
                onClick={() => redeem.mutate()}
                className="w-full rounded-lg border border-brand-teal-500/50 py-2 text-sm font-semibold text-brand-teal-200 hover:bg-brand-teal-600/20 disabled:opacity-50"
              >
                Redeem on behalf of customer
              </button>
            </div>

            {ledgerQ.data && ledgerQ.data.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                <h4 className="text-sm font-semibold text-white mb-2">Recent ledger</h4>
                <ul className="space-y-1.5 max-h-48 overflow-y-auto text-xs">
                  {ledgerQ.data.map((entry) => (
                    <li key={entry.id} className="flex justify-between gap-2 text-slate-300">
                      <span className="truncate">{entry.description || entry.source}</span>
                      <span className={entry.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                        {entry.amount >= 0 ? '+' : ''}
                        {entry.amount}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-xl border border-white/10 bg-white/5 p-8 text-center text-sm text-slate-500">
            Select a member to adjust points or redeem rewards.
          </div>
        )}
      </div>
    </div>
  )
}

function LoaderCenter() {
  return (
    <div className="flex justify-center py-12">
      <Loader2 className="w-6 h-6 animate-spin text-brand-teal-400" />
    </div>
  )
}
