'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Banknote,
  Clock,
  FileText,
  PiggyBank,
  PoundSterling,
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
import { accounts } from '@/lib/api-client'
import type { AxiosError } from 'axios'
import { formatCurrency } from '@/lib/utils'
import { ModuleCardGrid, type ModuleCardItem } from '@/components/modules/ModuleCardGrid'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { auth, tenants } from '@/lib/api-client'

type Dashboard = {
  headline: {
    revenue_30d_pence: number
    revenue_90d_pence: number
    revenue_ytd_pence: number
    outstanding_pence: number
    overdue_pence: number
    deals_open_pence: number
  }
  cashflow_daily: { date: string; paid_pence: number; invoiced_pence: number }[]
  upsell_suggestions: unknown[]
}

export function AccountsDashboard() {
  const [days, setDays] = useState(90)
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

  const { data, isLoading, isError, error, refetch } = useQuery<Dashboard>({
    queryKey: ['accounts-dashboard', days],
    queryFn: async () => {
      try {
        return (await accounts.dashboard(days)).data
      } catch (e) {
        const err = e as AxiosError
        if (err.response?.status === 404) {
          const { money } = await import('@/lib/api-client')
          return (await money.dashboard(days)).data
        }
        throw e
      }
    },
  })
  const errorDetail = isError
    ? String(
        (error as AxiosError<{ detail?: string }>).response?.data?.detail ??
          (error as AxiosError).message,
      )
    : null

  const h = data?.headline
  const cashIn = h?.revenue_30d_pence ?? 0
  const cashPending = h?.outstanding_pence ?? 0
  const cashOut = h?.overdue_pence ?? 0
  const cashSaved = Math.max(0, (h?.revenue_ytd_pence ?? 0) - (h?.outstanding_pence ?? 0))

  const cards: ModuleCardItem[] = [
    {
      title: 'Cash in',
      description: `Paid revenue in the last ${days} days — money received.`,
      href: '/dashboard/invoices',
      icon: ArrowDownLeft,
      badge: formatCurrency(cashIn),
    },
    {
      title: 'Cash pending',
      description: 'Outstanding invoices awaiting payment.',
      href: '/dashboard/invoices',
      icon: Clock,
      badge: formatCurrency(cashPending),
    },
    {
      title: 'Cash out',
      description: 'Overdue amounts — chase these first.',
      href: '/dashboard/invoices',
      icon: ArrowUpRight,
      badge: formatCurrency(cashOut),
    },
    {
      title: 'Cash saved',
      description: 'YTD collected minus still outstanding (working capital snapshot).',
      href: '/dashboard/accounts',
      icon: PiggyBank,
      badge: formatCurrency(cashSaved),
    },
    {
      title: 'Quotes',
      description: 'Send and track quotes before they become invoices.',
      href: '/dashboard/quotes',
      icon: FileText,
    },
    {
      title: 'Reports',
      description: 'Export-ready view of cashflow and pipeline value.',
      href: '/dashboard/accounts',
      icon: TrendingUp,
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-brand-forest-700 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-950/20 p-8 text-center">
        <p className="text-white font-semibold">Could not load accounts</p>
        <p className="text-sm text-brand-teal-100/70 mt-2">
          {errorDetail || 'Check your connection and try again.'}
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-4 rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-semibold text-white"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Accounts — cash position, collections, and reporting"
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-white">Accounts overview</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-lg border border-brand-forest-700 bg-brand-forest-950 px-3 py-2 text-sm text-white"
        >
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-5">
        <h3 className="text-sm font-bold text-white mb-1">Cashflow chart</h3>
        <p className="text-xs text-brand-teal-100/65 mb-4">Invoiced vs paid — colourful view of money movement</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.cashflow_daily}>
              <defs>
                <linearGradient id="accPaid" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#20ccce" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#20ccce" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="accInv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#025422" opacity={0.4} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#a7f3d0' }}
                tickFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}
              />
              <YAxis tick={{ fontSize: 10, fill: '#a7f3d0' }} tickFormatter={(v) => `£${(v / 100).toFixed(0)}`} />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Area type="monotone" dataKey="invoiced_pence" name="Invoiced" stroke="#10b981" fill="url(#accInv)" />
              <Area type="monotone" dataKey="paid_pence" name="Paid" stroke="#20ccce" fill="url(#accPaid)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <ModuleCardGrid items={cards} />

      {(h?.overdue_pence ?? 0) > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-950/20 p-4">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-white">Overdue: {formatCurrency(h!.overdue_pence)}</p>
            <Link href="/dashboard/invoices" className="text-xs text-brand-teal-300 hover:underline mt-1 inline-block">
              Review invoices →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
