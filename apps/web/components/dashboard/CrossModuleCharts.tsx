'use client'

import { useQuery } from '@tanstack/react-query'
import { crm, leads, money, reputation, tasks } from '@/lib/api-client'
import { ModuleMetricCharts, type MetricSeries } from '@/components/modules/ModuleMetricCharts'
import { formatCurrency } from '@/lib/utils'

export function CrossModuleCharts() {
  const { data: moneyData } = useQuery({
    queryKey: ['money-dashboard-30'],
    queryFn: () => money.dashboard(30).then((r) => r.data),
  })
  const { data: leadsData } = useQuery({
    queryKey: ['leads-count'],
    queryFn: () => leads.list({ page: 1, page_size: 1 }).then((r) => r.data),
  })
  const { data: pipeline } = useQuery({
    queryKey: ['pipeline'],
    queryFn: () => crm.pipeline().then((r) => r.data),
  })
  const { data: taskData } = useQuery({
    queryKey: ['tasks-open'],
    queryFn: () => tasks.list({ page: 1, page_size: 50, status: 'open' }).then((r) => r.data),
  })
  const { data: rep } = useQuery({
    queryKey: ['reputation-dashboard'],
    queryFn: () => reputation.dashboard().then((r) => r.data),
  })

  const chartData: MetricSeries[] = [
    {
      name: 'Leads',
      leads: leadsData?.total ?? 0,
    },
    {
      name: 'CRM',
      value: Math.round((pipeline?.total_value_pence ?? 0) / 100),
      booked: pipeline?.columns?.Booked?.length ?? 0,
    },
    {
      name: 'Tasks',
      tasks: taskData?.items?.length ?? taskData?.total ?? 0,
    },
    {
      name: 'Accounts',
      revenue: Math.round((moneyData?.headline?.revenue_30d_pence ?? 0) / 100),
    },
    {
      name: 'Reputation',
      reviews: rep?.total_reviews ?? 0,
    },
  ]

  return (
    <div className="space-y-4">
      <ModuleMetricCharts
        title="Business pulse"
        subtitle="Leads, CRM pipeline, tasks, accounts revenue (30d), and reputation — at a glance"
        data={chartData}
        seriesKeys={['leads', 'value', 'booked', 'tasks', 'revenue', 'reviews']}
      />
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'Leads', value: String(leadsData?.total ?? 0) },
          { label: 'Open deals', value: String(pipeline?.total_deals ?? 0) },
          { label: 'Pipeline', value: formatCurrency(pipeline?.total_value_pence ?? 0) },
          { label: 'Revenue 30d', value: formatCurrency(moneyData?.headline?.revenue_30d_pence ?? 0) },
          {
            label: 'Avg rating',
            value: rep?.avg_rating != null ? String(rep.avg_rating) : '—',
          },
        ].map((k) => (
          <div
            key={k.label}
            className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 px-4 py-3 text-center"
          >
            <p className="text-[10px] uppercase font-bold text-brand-teal-100/60">{k.label}</p>
            <p className="text-lg font-black text-white mt-1">{k.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
