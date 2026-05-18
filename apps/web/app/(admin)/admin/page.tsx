'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Activity, Building2, CreditCard, Users, FileText, Target,
  TrendingUp, AlertCircle,
} from 'lucide-react'
import { admin } from '@/lib/api-client'

interface PlatformStats {
  total_tenants: number
  active_tenants: number
  suspended_tenants: number
  total_users: number
  total_leads: number
  total_deals: number
  total_invoices: number
  paid_invoices_pence: number
  open_invoices_pence: number
  mrr_pence: number
  new_tenants_30d: number
}

function gbp(pence: number): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    maximumFractionDigits: 0,
  }).format(pence / 100)
}

function Stat({
  label, value, sublabel, icon: Icon, tone = 'default',
}: {
  label: string
  value: string | number
  sublabel?: string
  icon: any
  tone?: 'default' | 'good' | 'warn' | 'accent'
}) {
  const tones = {
    default: 'bg-gray-900 border-gray-800 text-gray-100',
    good:    'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
    warn:    'bg-amber-500/10 border-amber-500/30 text-amber-300',
    accent:  'bg-violet-500/10 border-violet-500/30 text-violet-300',
  } as const
  return (
    <div className={`rounded-xl border p-5 ${tones[tone]}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-gray-400 font-semibold">{label}</div>
          <div className="text-3xl font-bold mt-2">{value}</div>
          {sublabel && <div className="text-xs text-gray-500 mt-1">{sublabel}</div>}
        </div>
        <Icon className="w-5 h-5 opacity-60" />
      </div>
    </div>
  )
}

export default function AdminOverview() {
  const { data, isLoading, error } = useQuery<PlatformStats>({
    queryKey: ['admin', 'stats'],
    queryFn: () => admin.stats().then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-800 rounded w-64 animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-xl p-6 flex items-center gap-3">
        <AlertCircle className="w-5 h-5" />
        Failed to load platform stats.
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Platform overview</h1>
        <p className="text-gray-400 mt-1">Read-only metrics across every tenant. Live data.</p>
      </header>

      <section>
        <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-3">Revenue</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="MRR" value={gbp(data.mrr_pence)} icon={TrendingUp} tone="accent" sublabel="Active + trialing subs" />
          <Stat label="Paid invoices (total)" value={gbp(data.paid_invoices_pence)} icon={CreditCard} tone="good" />
          <Stat label="Open invoices" value={gbp(data.open_invoices_pence)} icon={FileText} tone="warn" />
          <Stat label="New tenants (30d)" value={data.new_tenants_30d} icon={Activity} />
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-3">Counts</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="Tenants (active)" value={`${data.active_tenants} / ${data.total_tenants}`} icon={Building2} />
          <Stat label="Users" value={data.total_users} icon={Users} />
          <Stat label="Leads" value={data.total_leads} icon={Target} />
          <Stat label="Deals" value={data.total_deals} icon={FileText} />
        </div>
      </section>

      {data.suspended_tenants > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 text-amber-300 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">
              {data.suspended_tenants} tenant{data.suspended_tenants === 1 ? '' : 's'} suspended.
            </span>
          </div>
          <a
            href="/admin/tenants?filter=suspended"
            className="text-xs font-semibold underline underline-offset-4 hover:text-amber-200"
          >
            Review →
          </a>
        </div>
      )}
    </div>
  )
}
