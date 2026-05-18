'use client'

import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowUpRight,
  Banknote,
  ChevronRight,
  Clock,
  PoundSterling,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { money } from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'

type Headline = {
  revenue_30d_pence: number
  revenue_90d_pence: number
  revenue_ytd_pence: number
  outstanding_pence: number
  overdue_pence: number
  deals_open_pence: number
}

type CashflowPoint = { date: string; paid_pence: number; invoiced_pence: number }

type Upsell = {
  customer_id: string
  name: string
  lifetime_value_pence: number
  last_deal_at: string | null
  reason: string
}

type Dashboard = {
  headline: Headline
  cashflow_daily: CashflowPoint[]
  upsell_suggestions: Upsell[]
}

const KPI_CARDS: Array<{
  key: keyof Headline
  label: string
  hint: string
  icon: typeof PoundSterling
  tint: string
}> = [
  { key: 'revenue_30d_pence', label: 'Revenue · 30d', hint: 'Last 30 days', icon: PoundSterling, tint: 'text-emerald-600 bg-emerald-100' },
  { key: 'revenue_90d_pence', label: 'Revenue · 90d', hint: 'Last 90 days', icon: TrendingUp, tint: 'text-brand-teal-100 bg-brand-teal-400/20' },
  { key: 'revenue_ytd_pence', label: 'Revenue · YTD', hint: 'Year to date', icon: Banknote, tint: 'text-indigo-600 bg-indigo-100' },
  { key: 'outstanding_pence', label: 'Outstanding', hint: 'Unpaid invoices', icon: Clock, tint: 'text-amber-600 bg-amber-100' },
  { key: 'overdue_pence', label: 'Overdue', hint: 'Past due date', icon: AlertTriangle, tint: 'text-red-600 bg-red-100' },
  { key: 'deals_open_pence', label: 'Pipeline value', hint: 'Open deals', icon: ArrowUpRight, tint: 'text-violet-600 bg-violet-100' },
]


export default function MoneyDashboardPage() {
  const { data, isLoading } = useQuery<Dashboard>({
    queryKey: ['money-dashboard'],
    queryFn: () => money.dashboard(90).then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Money Intelligence</h1>
        <p className="text-muted-foreground text-sm">Cashflow, outstanding balances, and AI-suggested upsells.</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {KPI_CARDS.map((card) => {
          const Icon = card.icon
          const value = data.headline[card.key] ?? 0
          return (
            <div key={card.key} className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wide text-brand-teal-100/75">
                  {card.label}
                </span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${card.tint}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <p className="mt-2 text-xl font-black text-white">{formatCurrency(value)}</p>
              <p className="text-[11px] text-brand-teal-100/60 mt-0.5">{card.hint}</p>
            </div>
          )
        })}
      </div>

      {/* Cashflow chart */}
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white">Cashflow — last 90 days</h2>
            <p className="text-xs text-brand-teal-100/70">Daily invoiced vs. paid totals.</p>
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.cashflow_daily} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="paid" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="invoiced" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `£${(Number(v) / 100).toFixed(0)}`}
              />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelFormatter={(label) => new Date(label).toLocaleDateString('en-GB')}
              />
              <Area
                type="monotone"
                dataKey="invoiced_pence"
                name="Invoiced"
                stroke="#3b82f6"
                fill="url(#invoiced)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="paid_pence"
                name="Paid"
                stroke="#10b981"
                fill="url(#paid)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Upsell suggestions */}
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 shadow-sm">
        <div className="px-5 py-4 border-b border-brand-forest-800 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand-teal-300" />
          <h2 className="text-sm font-bold text-white">AI-suggested upsells</h2>
        </div>
        <ul className="divide-y divide-brand-forest-800">
          {data.upsell_suggestions.length === 0 && (
            <li className="px-5 py-8 text-center text-sm text-brand-teal-100/60">
              No upsell opportunities right now. Check back as customers age.
            </li>
          )}
          {data.upsell_suggestions.map((s) => (
            <li key={s.customer_id} className="px-5 py-3 flex items-center gap-3 hover:bg-brand-forest-900">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">{s.name}</p>
                <p className="text-xs text-brand-teal-100/70 mt-0.5">{s.reason}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-white">{formatCurrency(s.lifetime_value_pence)}</p>
                <p className="text-[10px] text-brand-teal-100/60">LTV</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300" />
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
