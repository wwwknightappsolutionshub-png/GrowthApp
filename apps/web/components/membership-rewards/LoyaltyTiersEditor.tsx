'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Save } from 'lucide-react'
import { toast } from 'sonner'

import { membershipRewards } from '@/lib/api-client'

type TierRow = {
  id: string
  code: string
  name: string
  min_points_lifetime: number
  benefits: unknown[]
  sort_order: number
}

export function LoyaltyTiersEditor() {
  const qc = useQueryClient()
  const tiersQ = useQuery({
    queryKey: ['mr-tiers'],
    queryFn: async () => (await membershipRewards.listTiers()).data.items as TierRow[],
  })

  const [rows, setRows] = useState<TierRow[]>([])

  useEffect(() => {
    if (tiersQ.data) setRows(tiersQ.data)
  }, [tiersQ.data])

  const save = useMutation({
    mutationFn: async () => {
      await Promise.all(
        rows.map((row) =>
          membershipRewards.updateTier(row.id, {
            name: row.name,
            min_points_lifetime: row.min_points_lifetime,
          }),
        ),
      )
    },
    onSuccess: () => {
      toast.success('Loyalty tiers updated')
      qc.invalidateQueries({ queryKey: ['mr-tiers'] })
      qc.invalidateQueries({ queryKey: ['mr-landing'] })
    },
    onError: () => toast.error('Could not save tiers'),
  })

  if (tiersQ.isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-brand-teal-400" />
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-4">
      <div>
        <h3 className="text-base font-semibold text-white">Loyalty tiers</h3>
        <p className="text-sm text-slate-400 mt-1">
          Edit tier names and point thresholds shown on your public memberships page. Tier codes
          (Bronze, Silver, etc.) stay fixed for leaderboard tracking.
        </p>
      </div>

      <div className="space-y-3">
        {rows.map((row, i) => (
          <div
            key={row.id}
            className="grid gap-3 sm:grid-cols-[120px_1fr_140px] items-end rounded-lg border border-white/10 p-3"
          >
            <div>
              <span className="text-xs text-slate-500 uppercase tracking-wide">Code</span>
              <p className="text-sm font-medium text-slate-200 capitalize mt-1">{row.code}</p>
            </div>
            <label className="block">
              <span className="text-xs text-slate-400">Display name</span>
              <input
                value={row.name}
                onChange={(e) => {
                  const next = [...rows]
                  next[i] = { ...next[i], name: e.target.value }
                  setRows(next)
                }}
                className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              />
            </label>
            <label className="block">
              <span className="text-xs text-slate-400">Min lifetime points</span>
              <input
                type="number"
                min={0}
                value={row.min_points_lifetime}
                onChange={(e) => {
                  const next = [...rows]
                  next[i] = { ...next[i], min_points_lifetime: parseInt(e.target.value || '0', 10) }
                  setRows(next)
                }}
                className="mt-1 w-full rounded-lg border border-white/10 bg-brand-forest-950 px-3 py-2 text-sm text-white"
              />
            </label>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={() => save.mutate()}
        disabled={save.isPending}
        className="inline-flex items-center gap-2 rounded-lg bg-brand-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-teal-500 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {save.isPending ? 'Saving…' : 'Save tier changes'}
      </button>
    </div>
  )
}
