'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Building2, Search, ShieldOff, ShieldCheck, AlertCircle } from 'lucide-react'
import { admin } from '@/lib/api-client'

interface TenantSummary {
  id: string
  slug: string
  name: string
  business_type: string
  city: string | null
  postcode: string
  plan_name: string | null
  plan_price_pence: number
  subscription_status: string | null
  is_active: boolean
  onboarding_completed: boolean
  member_count: number
  lead_count: number
  deal_count: number
  invoice_total_pence: number
  created_at: string
}

function gbp(pence: number): string {
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(pence / 100)
}

function StatusPill({ active, sub }: { active: boolean; sub: string | null }) {
  if (!active) {
    return <span className="px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded bg-red-500/15 text-red-300 border border-red-500/30">Suspended</span>
  }
  const tone = sub === 'active'
    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
    : sub === 'trialing'
    ? 'bg-blue-500/15 text-blue-300 border-blue-500/30'
    : 'bg-gray-500/15 text-gray-400 border-gray-500/30'
  return <span className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded border ${tone}`}>{sub || 'unknown'}</span>
}

export default function AdminTenantsPage() {
  const [search, setSearch] = useState('')
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<TenantSummary[]>({
    queryKey: ['admin', 'tenants', search],
    queryFn: () => admin.listTenants({ q: search || undefined }).then((r) => r.data),
  })

  const suspend = useMutation({
    mutationFn: (id: string) => admin.suspendTenant(id),
    onSuccess: (res) => {
      toast.success((res.data as any).message || 'Tenant suspended')
      qc.invalidateQueries({ queryKey: ['admin', 'tenants'] })
      qc.invalidateQueries({ queryKey: ['admin', 'stats'] })
    },
    onError: () => toast.error('Failed to suspend tenant'),
  })

  const reactivate = useMutation({
    mutationFn: (id: string) => admin.reactivateTenant(id),
    onSuccess: (res) => {
      toast.success((res.data as any).message || 'Tenant reactivated')
      qc.invalidateQueries({ queryKey: ['admin', 'tenants'] })
      qc.invalidateQueries({ queryKey: ['admin', 'stats'] })
    },
    onError: () => toast.error('Failed to reactivate tenant'),
  })

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tenants</h1>
          <p className="text-gray-400 mt-1">Every business on the platform.</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or slug..."
            className="bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/40 w-72"
          />
        </div>
      </header>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5" /> Failed to load tenants.
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-950 text-xs uppercase tracking-wider text-gray-500">
            <tr>
              <th className="text-left px-5 py-3 font-semibold">Tenant</th>
              <th className="text-left px-5 py-3 font-semibold">Plan</th>
              <th className="text-left px-5 py-3 font-semibold">Status</th>
              <th className="text-right px-5 py-3 font-semibold">Members</th>
              <th className="text-right px-5 py-3 font-semibold">Leads</th>
              <th className="text-right px-5 py-3 font-semibold">Deals</th>
              <th className="text-right px-5 py-3 font-semibold">Invoiced</th>
              <th className="text-right px-5 py-3 font-semibold w-32">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && [...Array(4)].map((_, i) => (
              <tr key={i}>
                <td colSpan={8} className="px-5 py-4">
                  <div className="h-6 bg-gray-800 rounded animate-pulse" />
                </td>
              </tr>
            ))}
            {!isLoading && data?.length === 0 && (
              <tr>
                <td colSpan={8} className="px-5 py-12 text-center text-gray-500">
                  No tenants found.
                </td>
              </tr>
            )}
            {data?.map((t) => (
              <tr key={t.id} className="hover:bg-gray-800/50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-gray-400" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-100">{t.name}</div>
                      <div className="text-xs text-gray-500">
                        {t.business_type} · {t.city || t.postcode} · /{t.slug}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3">
                  <div className="text-gray-200">{t.plan_name || '—'}</div>
                  <div className="text-xs text-gray-500">{t.plan_price_pence ? `${gbp(t.plan_price_pence)}/mo` : ''}</div>
                </td>
                <td className="px-5 py-3"><StatusPill active={t.is_active} sub={t.subscription_status} /></td>
                <td className="px-5 py-3 text-right tabular-nums">{t.member_count}</td>
                <td className="px-5 py-3 text-right tabular-nums">{t.lead_count}</td>
                <td className="px-5 py-3 text-right tabular-nums">{t.deal_count}</td>
                <td className="px-5 py-3 text-right tabular-nums text-emerald-400">{gbp(t.invoice_total_pence)}</td>
                <td className="px-5 py-3 text-right">
                  {t.is_active ? (
                    <button
                      onClick={() => suspend.mutate(t.id)}
                      disabled={suspend.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 text-xs font-semibold border border-red-500/30 disabled:opacity-50"
                    >
                      <ShieldOff className="w-3.5 h-3.5" />
                      Suspend
                    </button>
                  ) : (
                    <button
                      onClick={() => reactivate.mutate(t.id)}
                      disabled={reactivate.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30 disabled:opacity-50"
                    >
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Reactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
