'use client'

import { useQuery } from '@tanstack/react-query'
import { crm } from '@/lib/api-client'
import { formatCurrency } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, Users, Target, BarChart3 } from 'lucide-react'
import { CrmDetailShell } from '@/components/crm/CrmDetailShell'

export default function CrmDashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['crm', 'dashboard'],
    queryFn: () => crm.dashboard().then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-teal-500 border-t-transparent" />
      </div>
    )
  }

  const widgets = [
    {
      title: 'New leads today',
      value: data?.new_leads_today ?? 0,
      icon: Users,
    },
    {
      title: 'Deals won (month)',
      value: data?.deals_won_this_month ?? 0,
      icon: Target,
    },
    {
      title: 'Pipeline value',
      value: formatCurrency(data?.total_pipeline_value_pence ?? 0),
      icon: TrendingUp,
    },
    {
      title: 'Lead sources',
      value: Object.keys(data?.leads_by_source ?? {}).length,
      icon: BarChart3,
      sub: 'active sources',
    },
  ]

  return (
    <CrmDetailShell title="CRM dashboard" subtitle="Performance at a glance">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {widgets.map((w) => (
          <Card key={w.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{w.title}</CardTitle>
              <w.icon className="h-4 w-4 text-brand-teal-600" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{w.value}</p>
              {w.sub && <p className="text-xs text-muted-foreground">{w.sub}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Leads by source</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(data?.leads_by_source ?? {}).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm">
                <span className="text-muted-foreground">{k}</span>
                <span className="font-semibold">{v as number}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Deals by stage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(data?.deals_by_stage ?? {}).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm">
                <span className="text-muted-foreground">{k}</span>
                <span className="font-semibold">{v as number}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </CrmDetailShell>
  )
}
