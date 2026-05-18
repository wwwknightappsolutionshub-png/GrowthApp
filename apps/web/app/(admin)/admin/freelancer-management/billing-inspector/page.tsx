'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Briefcase, Check, Pencil, RefreshCw, X } from 'lucide-react'
import { adminApi } from '@/lib/api-client'

interface BillingRow {
  id: string
  user_id: string
  user_email: string
  user_full_name: string
  estimated_client_count: number
  calculated_price: string | number
  override_price: string | number | null
  effective_price: string | number
  calculation_source: string
  created_at: string
}

function fmtGBP(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(n)) return String(value)
  return `£${n.toFixed(2)}`
}

function fmtDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function BillingInspectorPage() {
  const qc = useQueryClient()
  const billings = useQuery({
    queryKey: ['admin', 'freelancer-management', 'billings'],
    queryFn: () => adminApi.freelancerBillings().then((r) => r.data as BillingRow[]),
  })

  const [editingId, setEditingId] = useState<string | null>(null)
  const [draftValue, setDraftValue] = useState<string>('')

  const updateOverride = useMutation({
    mutationFn: ({ id, value }: { id: string; value: number | null }) =>
      adminApi.setFreelancerBillingOverride(id, value),
    onSuccess: () => {
      toast.success('Override updated')
      setEditingId(null)
      setDraftValue('')
      qc.invalidateQueries({ queryKey: ['admin', 'freelancer-management', 'billings'] })
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Could not update override'
      toast.error(String(msg))
    },
  })

  const rows = billings.data ?? []

  return (
    <div className="text-white">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-amber-400" /> Billing Inspector
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Review every freelancer&apos;s estimated client count and calculated subscription price.
            Override any row manually — leave override blank to restore the auto-calculated price.
          </p>
        </div>
        <button
          onClick={() => billings.refetch()}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Stat label="Total freelancers" value={rows.length} />
        <Stat
          label="Auto-priced"
          value={rows.filter((r) => r.calculation_source === 'auto').length}
        />
        <Stat
          label="Manually overridden"
          value={rows.filter((r) => r.calculation_source === 'manual').length}
        />
        <Stat
          label="Avg effective price"
          value={
            rows.length === 0
              ? '—'
              : fmtGBP(
                  rows.reduce((a, b) => a + Number(b.effective_price), 0) / rows.length,
                )
          }
        />
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-800 text-sm">
            <thead className="bg-gray-950/60 text-xs uppercase tracking-wider text-gray-500">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Freelancer</th>
                <th className="px-4 py-3 text-right font-semibold">Est. clients</th>
                <th className="px-4 py-3 text-right font-semibold">Calculated</th>
                <th className="px-4 py-3 text-right font-semibold">Override</th>
                <th className="px-4 py-3 text-right font-semibold">Effective</th>
                <th className="px-4 py-3 text-left font-semibold">Source</th>
                <th className="px-4 py-3 text-left font-semibold">Created</th>
                <th className="px-4 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {billings.isLoading && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-gray-500">
                    Loading freelancer billings…
                  </td>
                </tr>
              )}
              {billings.isError && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-red-400">
                    Could not load billings.
                  </td>
                </tr>
              )}
              {!billings.isLoading && rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-gray-500">
                    No freelancer billing records yet.
                  </td>
                </tr>
              )}
              {rows.map((row) => {
                const isEditing = editingId === row.id
                const isManual = row.calculation_source === 'manual'
                return (
                  <tr key={row.id} className="hover:bg-gray-950/40">
                    <td className="px-4 py-3 align-top">
                      <div className="font-medium">{row.user_full_name}</div>
                      <div className="text-xs text-gray-500">{row.user_email}</div>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {row.estimated_client_count}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                      {fmtGBP(row.calculated_price)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {isEditing ? (
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={draftValue}
                          onChange={(e) => setDraftValue(e.target.value)}
                          autoFocus
                          placeholder="(blank = clear)"
                          className="w-28 rounded border border-gray-700 bg-gray-950 px-2 py-1 text-right text-white focus:border-amber-500 focus:outline-none"
                        />
                      ) : row.override_price !== null ? (
                        <span className="text-amber-300">{fmtGBP(row.override_price)}</span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold">
                      {fmtGBP(row.effective_price)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          isManual
                            ? 'inline-flex items-center rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300'
                            : 'inline-flex items-center rounded-full bg-gray-800 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400'
                        }
                      >
                        {row.calculation_source}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{fmtDate(row.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      {isEditing ? (
                        <div className="inline-flex gap-1">
                          <button
                            onClick={() => {
                              const trimmed = draftValue.trim()
                              const value = trimmed === '' ? null : Number(trimmed)
                              if (value !== null && (Number.isNaN(value) || value < 0)) {
                                toast.error('Enter a non-negative number, or blank to clear')
                                return
                              }
                              updateOverride.mutate({ id: row.id, value })
                            }}
                            disabled={updateOverride.isPending}
                            className="inline-flex items-center gap-1 rounded bg-amber-500 px-2 py-1 text-xs font-semibold text-gray-950 hover:bg-amber-400 disabled:opacity-60"
                          >
                            <Check className="h-3 w-3" /> Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingId(null)
                              setDraftValue('')
                            }}
                            className="inline-flex items-center gap-1 rounded border border-gray-700 px-2 py-1 text-xs text-gray-400 hover:bg-gray-800"
                          >
                            <X className="h-3 w-3" /> Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setEditingId(row.id)
                            setDraftValue(
                              row.override_price === null ? '' : String(row.override_price),
                            )
                          }}
                          className="inline-flex items-center gap-1 rounded border border-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800"
                        >
                          <Pencil className="h-3 w-3" />{' '}
                          {row.override_price === null ? 'Override' : 'Edit'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <div className="text-[10px] uppercase tracking-widest text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
    </div>
  )
}
