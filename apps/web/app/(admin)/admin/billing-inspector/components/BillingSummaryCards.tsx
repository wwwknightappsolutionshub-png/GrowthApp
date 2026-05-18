'use client'

import { AlertTriangle, BadgePoundSterling, Briefcase, Building2, Clock, XCircle } from 'lucide-react'

export interface OverviewData {
  total_tenants: number
  total_freelancers: number
  total_mrr_gbp: number
  tenant_mrr_gbp: number
  freelancer_mrr_gbp: number
  upcoming_invoices_count: number
  overdue_invoices_count: number
  recent_payment_failures: Array<{
    invoice_id: string
    tenant_id: string
    amount_pence: number
    status: string
    created_at: string | null
  }>
  global_overage_alerts: Array<{
    entity_type: string
    entity_id: string
    entity_name: string
    flag: string
  }>
}

function fmtGBP(n: number): string {
  if (n === null || n === undefined) return '—'
  return `£${Number(n).toLocaleString('en-GB', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

export function BillingSummaryCards({ data }: { data?: OverviewData }) {
  const cards = [
    {
      label: 'Total tenants',
      value: data ? data.total_tenants : '—',
      Icon: Building2,
    },
    {
      label: 'Total freelancers',
      value: data ? data.total_freelancers : '—',
      Icon: Briefcase,
    },
    {
      label: 'Total MRR',
      value: data ? fmtGBP(data.total_mrr_gbp) : '—',
      sub: data
        ? `Tenants ${fmtGBP(data.tenant_mrr_gbp)} · Freelancers ${fmtGBP(data.freelancer_mrr_gbp)}`
        : null,
      Icon: BadgePoundSterling,
    },
    {
      label: 'Upcoming invoices',
      value: data ? data.upcoming_invoices_count : '—',
      sub: 'Next 30 days',
      Icon: Clock,
    },
    {
      label: 'Overdue invoices',
      value: data ? data.overdue_invoices_count : '—',
      Icon: XCircle,
    },
    {
      label: 'Global overage alerts',
      value: data ? data.global_overage_alerts.length : '—',
      Icon: AlertTriangle,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {cards.map(({ label, value, sub, Icon }) => (
        <div key={label} className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-gray-500">
            <Icon className="h-3.5 w-3.5 text-amber-400" />
            {label}
          </div>
          <div className="mt-1 text-2xl font-bold tabular-nums text-white">{value}</div>
          {sub ? <div className="mt-1 text-[11px] text-gray-500">{sub}</div> : null}
        </div>
      ))}
    </div>
  )
}
